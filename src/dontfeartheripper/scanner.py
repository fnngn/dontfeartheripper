from pathlib import Path

from .models import LibraryItem
from .toc import parse_toc
from .tags import read_flac_tags
from .utils import sanitize_filename
from .nfo import parse_album_nfo


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


def scan_library(root: Path) -> list:
    items = []

    for category in ("album", "compilation", "soundtrack"):
        cat_path = root / category

        if not cat_path.exists():
            continue

        for album in cat_path.iterdir():
            if not album.is_dir():
                continue

            flacs = list(album.glob("*.flac"))
            subdirs = [p for p in album.iterdir() if p.is_dir()]

            toc = list(album.glob("*.toc")) + list(album.glob("*.TOC"))
            cue = list(album.glob("*.cue")) + list(album.glob("*.CUE"))

            disc_number = None

            nfo_file = album / "album.nfo"
            if nfo_file.exists():
                nfo = parse_album_nfo(nfo_file)
                disc_number = nfo["disc"]

            cryptic = "~" in album.name

            album_name = None
            artist_name = None
            track_count = 0
            metadata_source = "unknown"

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

            if flacs and (
                album_name is None
                or artist_name is None
                or is_low_quality_metadata(
                    artist_name,
                    album_name,
                )
            ):
                tags = read_flac_tags(flacs[0])

                low_quality = is_low_quality_metadata(
                    artist_name,
                    album_name,
                )

                if low_quality:
                    artist_name = (
                        tags["albumartist"]
                        or tags["artist"]
                    )
                    album_name = tags["album"]
                    metadata_source = "flac"

                else:
                    if tags["albumartist"]:
                        artist_name = tags["albumartist"]
                        metadata_source = "flac"

                    if album_name is None:
                        album_name = tags["album"]

                    if artist_name is None:
                        artist_name = tags["artist"]

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
                    disc_number=disc_number,
                    container_directory=container_directory,
                    metadata_source=metadata_source,
                    rename_candidate=rename_candidate,
                    suggested_name=suggested_name,
                    track_count=track_count,
                )
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

    return items
