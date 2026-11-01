import json

from pathlib import Path

from mutagen.flac import FLAC
from .progress import ProgressCallback, report_progress
from .atomic import atomic_write_text
from .container import resolve_container_context
from .recovery import (
    build_recovery_candidate,
    build_repair_operations,
    build_full_repair_operations,
)
from .nfo import parse_album_nfo
from .tags2 import TrackMetadata

REPAIR_UNDO_FILE = Path(".dftr-last-repair.json")


def find_flac_files(directory):
    return sorted(
        str(path)
        for path in directory.glob("*")
        if path.is_file()
        and path.suffix.lower() == ".flac"
    )




def find_nearest_album_nfo(
    start_path,
):

    current = Path(
        start_path
    ).resolve()

    for directory in (
        current,
        *current.parents,
    ):

        candidate = (
            directory
            / "album.nfo"
        )

        if candidate.exists():
            return candidate

    return None



def analyze_repairs(
    items,
    progress: ProgressCallback | None = None,
):
    repairs = []
    total = len(items)

    for index, item in enumerate(items, start=1):
        if index == 1 or index % 20 == 0 or index == total:
            report_progress(
                progress,
                f"Checking repair rules: {item.path.name}",
                index,
                total,
            )

        artist = item.artist_name or ""
        files = find_flac_files(item.path)

        if artist == "VARIOUS":
            repairs.append(
                {
                    "path": str(item.path),
                    "files": files,
                    "field": "albumartist",
                    "old": artist,
                    "new": "Various Artists",
                    "rule": "various_uppercase",
                    "safe": True,
                }
            )

        elif artist == "Various":
            repairs.append(
                {
                    "path": str(item.path),
                    "files": files,
                    "field": "albumartist",
                    "old": artist,
                    "new": "Various Artists",
                    "rule": "various_mixed",
                    "safe": True,
                }
            )

        if (
            artist == ""
            and not item.container_directory
        ):
            parts = item.path.name.split(" - ", 1)

            if len(parts) == 2:
                inferred_artist = parts[0].strip()

                if inferred_artist:
                    repairs.append(
                        {
                            "path": str(item.path),
                            "files": files,
                            "field": "artist",
                            "old": "",
                            "new": inferred_artist,
                            "rule": "missing_artist",
                            "safe": True,
                        }
                    )



    #
    # recovery engine
    #

    for index, item in enumerate(items, start=1):
        if index == 1 or index % 20 == 0 or index == total:
            report_progress(
                progress,
                f"Checking metadata recovery: {item.path.name}",
                index,
                total,
            )

        if item.container_directory:
            continue

        context = resolve_container_context(
            item.path
        )

        if not context:
            continue

        local = TrackMetadata(
            artist=item.artist_name,
            album=item.album_name,
        )

        nfo_metadata = {}

        nfo_file = (
            find_nearest_album_nfo(
                item.path
            )
        )

        if (
            nfo_file
            and nfo_file.exists()
        ):

            try:

                nfo_data = parse_album_nfo(
                    nfo_file
                )

                if (
                    nfo_data
                    and nfo_data.get(
                        "artist"
                    )
                ):

                    nfo_metadata[
                        "artist"
                    ] = (
                        nfo_data[
                            "artist"
                        ]
                    )

                if (
                    nfo_data
                    and nfo_data.get(
                        "album"
                    )
                ):

                    nfo_metadata[
                        "album"
                    ] = (
                        nfo_data[
                            "album"
                        ]
                    )

                if (
                    nfo_data
                    and nfo_data.get(
                        "albumartist"
                    )
                ):

                    nfo_metadata[
                        "albumartist"
                    ] = (
                        nfo_data[
                            "albumartist"
                        ]
                    )

            except Exception:

                pass

        container_metadata = {}

        if (
            context
            and context.get(
                "container_type"
            )
            == "artist_container"
        ):

            artist_name = (
                context.get(
                    "name",
                    ""
                )
            )

            DISCGRAPHY_SUFFIXES = (
                " - Discography",
                " Discography",
                " - Diskographie",
                " Diskographie",
                " Complete Discography",
                " Collection",
                " Anthology",
            )

            for suffix in DISCGRAPHY_SUFFIXES:

                if artist_name.endswith(
                    suffix
                ):
                    artist_name = (
                        artist_name[
                            :-len(suffix)
                        ]
                    ).strip()

            container_metadata = {
                "artist":
                    artist_name,
                "albumartist":
                    artist_name,
            }

        candidate = build_recovery_candidate(
            local,
            container_metadata=
                container_metadata,
            nfo_metadata=
                nfo_metadata,
        )

        recovery_repairs = (
            build_full_repair_operations(
                local,
                candidate,
            )
        )

        for repair in recovery_repairs:

            repairs.append(
                {
                    "path": str(item.path),
                    "files": find_flac_files(
                        item.path
                    ),
                    "field": repair["field"],
                    "old": repair["old"] or "",
                    "new": repair["new"],
                    "rule": repair["rule"],
                    "safe": True,
                }
            )

    return {
        "schema_version": 1,
        "repairs": repairs,
    }


def save_repair_log(entries):
    atomic_write_text(
        REPAIR_UNDO_FILE,
        json.dumps(entries, indent=2),
    )


def load_repair_log():
    if not REPAIR_UNDO_FILE.exists():
        return []

    return json.loads(
        REPAIR_UNDO_FILE.read_text()
    )


def apply_repairs(
    repairs,
    progress: ProgressCallback | None = None,
):
    rollback = []
    applied = 0
    files = [
        file_path
        for repair in repairs
        for file_path in repair["files"]
    ]
    total = len(files)
    report_progress(progress, "Preparing tag repairs", 0, total)

    for repair in repairs:

        field = repair["field"]

        for file_path in repair["files"]:

            file = Path(file_path)

            if not file.exists():
                continue

            report_progress(
                progress,
                f"Updating tags: {file.name}",
                applied,
                total,
            )
            audio = FLAC(file)

            old_value = ""

            if field in audio:
                values = audio[field]

                if values:
                    old_value = values[0]

            rollback.append(
                {
                    "file": str(file),
                    "field": field,
                    "old": old_value,
                    "new": repair["new"],
                    "rule": repair["rule"],
                }
            )
            save_repair_log(rollback)

            audio[field] = [repair["new"]]
            audio.save()

            applied += 1
            report_progress(
                progress,
                f"Updated tags: {file.name}",
                applied,
                total,
            )

    return applied


def undo_repairs(progress: ProgressCallback | None = None):
    rollback = load_repair_log()

    reverted = 0
    total = len(rollback)

    for index, entry in enumerate(reversed(rollback), start=1):

        file = Path(entry["file"])

        if not file.exists():
            continue

        report_progress(
            progress,
            f"Restoring tags: {file.name}",
            index - 1,
            total,
        )
        audio = FLAC(file)

        field = entry["field"]
        old_value = entry["old"]

        if old_value:
            audio[field] = [old_value]
        else:
            if field in audio:
                del audio[field]

        audio.save()

        reverted += 1
        report_progress(
            progress,
            f"Restored tags: {file.name}",
            index,
            total,
        )

    return reverted
