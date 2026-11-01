from pathlib import Path

from .container import AUDIO_EXTENSIONS, count_album_nodes, detect_containers
from .models import LibraryItem
from .progress import ProgressCallback, report_progress
from .tags2 import read_tags


def search_library(
    root: Path,
    items: list[LibraryItem],
    query: str,
    progress: ProgressCallback | None = None,
) -> list[str]:
    needle = query.strip().casefold()
    if not needle:
        return []

    results = []
    seen = set()

    def add(key, result):
        if key not in seen:
            seen.add(key)
            results.append(result)

    report_progress(progress, "Finding collections")
    for collection in detect_containers(root, progress):
        name = Path(collection["path"]).name
        if needle in name.casefold():
            album_count = count_album_nodes(collection["children"])
            add(
                ("collection", str(collection["path"])),
                f"COLLECTION  {name} · {album_count} albums",
            )

    audio_files = []
    for item in items:
        artist = item.artist_name or item.path.parent.name
        album = item.album_name or item.path.name
        if needle in artist.casefold():
            add(("artist", artist.casefold()), f"ARTIST  {artist}")
        if needle in album.casefold():
            add(
                ("album", str(item.path)),
                f"ALBUM  {artist} — {album}  [{item.category}]",
            )
        if item.genre and needle in item.genre.casefold():
            add(
                ("genre", item.genre.casefold(), str(item.path)),
                f"GENRE  {item.genre} — {artist} / {album}",
            )
        if item.path.is_dir():
            audio_files.extend(
                (item, path)
                for path in sorted(item.path.iterdir())
                if path.is_file()
                and path.suffix.lower() in AUDIO_EXTENSIONS
            )
    total = len(audio_files)
    report_progress(
        progress,
        "Searching track titles, artists, and genres",
        0,
        total,
    )

    for index, (item, audio_path) in enumerate(audio_files, start=1):
        if index == 1 or index % 20 == 0 or index == total:
            report_progress(
                progress,
                f"Searching track tags · {item.path.name}",
                index,
                total,
            )

        metadata = read_tags(audio_path)
        album = metadata.album or item.album_name or item.path.name
        artist = (
            metadata.artist
            or metadata.albumartist
            or item.artist_name
            or item.path.parent.name
        )
        title = metadata.title or audio_path.stem
        genre = metadata.genre or item.genre

        if needle in artist.casefold():
            add(("artist", artist.casefold()), f"ARTIST  {artist}")
        if needle in album.casefold():
            add(
                ("album", str(item.path)),
                f"ALBUM  {artist} — {album}  [{item.category}]",
            )
        if needle in title.casefold():
            add(
                ("song", str(audio_path)),
                f"SONG  {artist} — {title}  [{album}]",
            )
        if genre and needle in genre.casefold():
            add(
                ("genre", genre.casefold(), str(item.path)),
                f"GENRE  {genre} — {artist} / {album}",
            )

    report_progress(
        progress,
        f"Search complete · {len(results)} matches",
        len(audio_files),
        len(audio_files),
    )
    return results
