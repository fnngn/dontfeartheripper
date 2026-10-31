from pathlib import Path

from mutagen.flac import FLAC

def read_flac_tags(path: Path) -> dict:
    try:
        audio = FLAC(path)

        return {
            "artist": (audio.get("ARTIST") or [None])[0],
            "albumartist": (audio.get("ALBUMARTIST") or [None])[0],
            "album": (audio.get("ALBUM") or [None])[0],
            "title": (audio.get("TITLE") or [None])[0],
        }

    except Exception:
        return {
            "artist": None,
            "albumartist": None,
            "album": None,
            "title": None,
        }
