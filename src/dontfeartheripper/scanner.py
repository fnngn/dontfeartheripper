from pathlib import Path

from .models import LibraryItem
from .toc import parse_toc
from .tags import read_flac_tags

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

            cryptic = "~" in album.name

            album_name = None
            artist_name = None
            track_count = 0
            container_directory = len(flacs) == 0 and len(subdirs) > 0

            if toc:
                meta = parse_toc(toc[0])
                album_name = meta["album"]
                artist_name = meta["artist"]
                track_count = meta["tracks"]

            if flacs and (album_name is None or artist_name is None):
                tags = read_flac_tags(flacs[0])

                if tags["albumartist"]:
                    artist_name = tags["albumartist"]


                if album_name is None:
                    album_name = tags["album"]

                if artist_name is None:
                    artist_name = tags["artist"]



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
                    container_directory=container_directory,
                    track_count=track_count,
                )
            )

    return items
