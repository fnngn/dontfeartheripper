import re
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

import requests


USER_AGENT = "dontfeartheripper/0.1.2"


def normalize_query(value):
    if not value:
        return value

    value = re.sub(
        r"\s+-\s+CD\s+\d+$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"\\([^)]*\\)",
        "",
        value,
    )

    value = re.sub(
        r"original motion picture soundtrack",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"soundtrack$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def release_cover_url(mbid):

    try:

        response = requests.get(
            f"https://coverartarchive.org/release/{mbid}",
            timeout=10,
        )

        if response.status_code != 200:
            return None

        data = response.json()

        images = data.get(
            "images",
            [],
        )

        if not images:
            return None

        return images[0].get(
            "image"
        )

    except requests.RequestException:
        return None




def _cover_lookup(release):

    return (
        release,
        release_cover_url(
            release["id"]
        ),
    )




def _lookup(query):

    response = requests.get(
        "https://musicbrainz.org/ws/2/release/",
        params={
            "query": query,
            "fmt": "json",
            "limit": 10,
        },
        headers={
            "User-Agent": USER_AGENT,
        },
        timeout=10,
    )

    response.raise_for_status()

    releases = response.json().get(
        "releases",
        [],
    )

    if not releases:
        return None

    release = releases[0]

    cover_url = release_cover_url(
        release["id"]
    )

    return {
        "id": release["id"],
        "title": release["title"],
        "release_count": len(releases),
        "selected_has_cover": bool(
            cover_url
        ),
        "cover_url": cover_url,
    }


def search_release(artist, album):

    artist = normalize_query(artist)
    album = normalize_query(album)

    if not album:
        return None

    queries = []

    if artist:
        queries.append(
            f'artist:"{artist}" release:"{album}"'
        )

    queries.append(
        f'release:"{album}"'
    )

    for query in queries:

        try:

            result = _lookup(query)

            if result:
                return result

        except requests.RequestException:
            pass

    return None
