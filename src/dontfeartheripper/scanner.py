from pathlib import Path

from .models import LibraryItem
from .toc import parse_toc
from .tags2 import read_tags
from .utils import sanitize_filename
from .nfo import parse_album_nfo
from .progress import ProgressCallback, report_progress


def is_low_quality_metadata(artist: str | None, album: str | None) -> bool:
    if not artist:
        return True

    if not album:
        return True

    if artist in (
        "Various",
        "VARIOUS",
    ):
        return True

    if album.startswith("MBB"):
        return True

    return False




AUDIO_EXTENSIONS = {
    ".flac",
    ".mp3",
    ".m4a",
    ".aac",
    ".ogg",
    ".opus",
    ".wav",
    ".ape",
    ".wv",
}


def has_audio_files(directory):

    try:

        for item in directory.iterdir():

            if (
                item.is_file()
                and item.suffix.lower()
                in AUDIO_EXTENSIONS
            ):
                return True

    except Exception:

        pass

    return False


def iter_album_dirs(root_directory, progress=None):

    seen = set()
    visited = 0

    for path in root_directory.rglob("*"):

        if not path.is_dir():
            continue

        visited += 1
        if visited == 1 or visited % 100 == 0:
            report_progress(
                progress,
                f"Searching {path}",
                visited,
            )

        has_album_content = (
            has_audio_files(path)
            or list(path.glob("*.cue"))
            or list(path.glob("*.CUE"))
            or list(path.glob("*.toc"))
            or list(path.glob("*.TOC"))
            or (path / "album.nfo").exists()
        )

        if not has_album_content:
            continue

        resolved = path.resolve()

        if resolved in seen:
            continue

        seen.add(resolved)

        yield path




def find_nearest_album_nfo(start):

    current = Path(start)

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



def scan_library(
    root: Path,
    progress: ProgressCallback | None = None,
) -> list:
    items = []
    scanned = 0

    for category in ("album", "compilation", "soundtrack"):
        cat_path = root / category

        if not cat_path.exists():
            continue

        report_progress(progress, f"Scanning {category} folders")
        for album in iter_album_dirs(
            cat_path,
            progress,
        ):

            audio_files = sorted(
                path
                for path in album.iterdir()
                if path.is_file()
                and path.suffix.lower() in AUDIO_EXTENSIONS
            )
            flacs = [
                path
                for path in audio_files
                if path.suffix.lower() == ".flac"
            ]
            subdirs = [p for p in album.iterdir() if p.is_dir()]

            toc = list(album.glob("*.toc")) + list(album.glob("*.TOC"))
            cue = list(album.glob("*.cue")) + list(album.glob("*.CUE"))

            disc_number = None

            nfo_file = find_nearest_album_nfo(
                album
            )

            nfo = None

            if (
                nfo_file
                and nfo_file.exists()
            ):
                nfo = parse_album_nfo(
                    nfo_file
                )
                disc_number = nfo["disc"]

            cryptic = "~" in album.name

            album_name = None
            artist_name = None
            genre = None
            track_count = len(audio_files)
            metadata_source = "unknown"

            if nfo:

                if nfo.get("artist"):
                    artist_name = (
                        nfo["artist"]
                    )

                if nfo.get("album"):
                    album_name = (
                        nfo["album"]
                    )
                genre = nfo.get("genre")

                metadata_source = "nfo"

            container_directory = (
                len(flacs) == 0 and len(subdirs) > 0
            )

            rename_candidate = False
            suggested_name = None

            if toc:
                meta = parse_toc(toc[0])

                album_name = meta["album"]
                artist_name = meta["artist"]
                track_count = meta["tracks"]

                if album_name or artist_name:
                    metadata_source = "toc"

            if audio_files and (
                album_name is None
                or artist_name is None
                or is_low_quality_metadata(
                    artist_name,
                    album_name,
                )
            ):
                tags = read_tags(audio_files[0])

                low_quality = is_low_quality_metadata(
                    artist_name,
                    album_name,
                )

                if low_quality:
                    artist_name = (
                        tags.albumartist
                        or tags.artist
                    )
                    album_name = tags.album
                    metadata_source = tags.source_format

                else:
                    if tags.albumartist:
                        artist_name = tags.albumartist
                        metadata_source = tags.source_format

                    if album_name is None:
                        album_name = tags.album

                    if artist_name is None:
                        artist_name = tags.artist

                    if tags.source_format != "unknown":
                        metadata_source = tags.source_format

            if cryptic and artist_name and album_name:
                album_upper = album_name.upper()

                has_disc_in_name = (
                    disc_number
                    and f"CD {disc_number}" in album_upper
                )

                if (
                    disc_number
                    and disc_number > 1
                    and not has_disc_in_name
                ):
                    suggested_name = sanitize_filename(
                        f"{artist_name} - {album_name} - CD {disc_number}"
                    )
                else:
                    suggested_name = sanitize_filename(
                        f"{artist_name} - {album_name}"
                    )

                rename_candidate = True

            items.append(
                LibraryItem(
                    path=album,
                    flac_count=len(flacs),
                    has_toc=bool(toc),
                    has_cue=bool(cue),
                    category=category,
                    cryptic=cryptic,
                    album_name=album_name,
                    artist_name=artist_name,
                    genre=genre,
                    disc_number=disc_number,
                    container_directory=container_directory,
                    metadata_source=metadata_source,
                    rename_candidate=rename_candidate,
                    suggested_name=suggested_name,
                    track_count=track_count,
                )
            )
            scanned += 1
            report_progress(
                progress,
                f"Read tags: {album.name}",
                scanned,
            )

    seen = {}

    for item in items:
        if not item.rename_candidate:
            continue

        collision_key = (
            item.category,
            item.path.parent,
            item.suggested_name,
        )

        if collision_key in seen:
            item.rename_collision = True
            seen[collision_key].rename_collision = True
        else:
            seen[collision_key] = item

    report_progress(
        progress,
        f"Scan complete: {len(items)} library entries",
        len(items),
        len(items),
    )
    return items
