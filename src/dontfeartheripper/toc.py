from pathlib import Path

def parse_toc(path: Path) -> dict:
    album = None
    artist = None
    tracks = 0

    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()

            if album is None and line.startswith("TITLE "):
                try:
                    album = line.split("\"")[1]
                except IndexError:
                    pass

            if artist is None and line.startswith("PERFORMER "):
                try:
                    artist = line.split("\"")[1]
                except IndexError:
                    pass

            if line.startswith("// Track "):
                tracks += 1

    return {
        "album": album,
        "artist": artist,
        "tracks": tracks,
    }
