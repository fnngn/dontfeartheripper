import json

from pathlib import Path

from mutagen.flac import FLAC

REPAIR_UNDO_FILE = Path(".dftr-last-repair.json")


def find_flac_files(directory):
    return sorted(
        str(path)
        for path in directory.glob("*.flac")
        if path.is_file()
    )


def analyze_repairs(items):
    repairs = []

    for item in items:

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

    return {
        "schema_version": 1,
        "repairs": repairs,
    }


def save_repair_log(entries):
    REPAIR_UNDO_FILE.write_text(
        json.dumps(entries, indent=2)
    )


def load_repair_log():
    if not REPAIR_UNDO_FILE.exists():
        return []

    return json.loads(
        REPAIR_UNDO_FILE.read_text()
    )


def apply_repairs(repairs):
    rollback = []
    applied = 0

    for repair in repairs:

        field = repair["field"]

        for file_path in repair["files"]:

            file = Path(file_path)

            if not file.exists():
                continue

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

            audio[field] = [repair["new"]]
            audio.save()

            applied += 1

    save_repair_log(rollback)

    return applied


def undo_repairs():
    rollback = load_repair_log()

    reverted = 0

    for entry in reversed(rollback):

        file = Path(entry["file"])

        if not file.exists():
            continue

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

    return reverted
