import json

from pathlib import Path


CACHE_FILE = Path(".dftr-cover-cache.json")
MBID_CACHE_FILE = Path(".dftr-mbid-cache.json")


def load_cover_cache():

    if not CACHE_FILE.exists():
        return {}

    try:
        return json.loads(
            CACHE_FILE.read_text()
        )
    except Exception:
        return {}


def save_cover_cache(cache):

    CACHE_FILE.write_text(
        json.dumps(
            cache,
            indent=2,
        )
    )


def load_mbid_cache():

    if not MBID_CACHE_FILE.exists():
        return {}

    try:
        return json.loads(
            MBID_CACHE_FILE.read_text()
        )
    except Exception:
        return {}


def save_mbid_cache(cache):

    MBID_CACHE_FILE.write_text(
        json.dumps(
            cache,
            indent=2,
        )
    )


def cache_key(artist, album):

    return f"{artist}|{album}"
