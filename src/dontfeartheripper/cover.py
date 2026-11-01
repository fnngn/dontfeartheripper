import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from pathlib import Path

from .musicbrainz import search_release
from .cover_cache import (
    load_cover_cache,
    save_cover_cache,
    cache_key,
)

from .artwork_sources import (
    coverartarchive_cover,
    discogs_cover,
)


COVER_PATTERNS = (
    "cover",
    "folder",
    "front",
    "artwork",
    "albumart",
)

IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
)



def find_existing_cover(directory):

    #
    # Fast path:
    # root directory first
    #

    candidates = sorted(directory.iterdir())

    #
    # Fallback:
    # search a few levels deep
    #

    candidates.extend(
        sorted(
            p
            for p in directory.rglob("*")
            if p.parent != directory
        )
    )

    for path in candidates:

        if not path.is_file():
            continue

        suffix = (
            path.suffix.lower()
        )

        if suffix not in IMAGE_EXTENSIONS:
            continue

        stem = (
            path.stem.lower()
        )

        for pattern in COVER_PATTERNS:

            if pattern in stem:
                return path

    return None


def has_cover(directory):
    return find_existing_cover(directory) is not None


def cover_target(directory):
    return directory / "cover.jpg"


def normalize_album_name(name):
    if not name:
        return ""

    return re.sub(
        r"\s+-\s+CD\s+\d+$",
        "",
        name,
        flags=re.IGNORECASE,
    )


def analyze_covers(items):
    missing = []
    seen = set()

    for item in items:

        if item.container_directory:
            continue

        existing = find_existing_cover(
            item.path
        )

        if existing:
            continue

        key = (
            item.artist_name or "",
            normalize_album_name(
                item.album_name or item.path.name
            ),
        )

        if key in seen:
            continue

        seen.add(key)

        missing.append(
            {
                "path": str(item.path),
                "artist": item.artist_name,
                "album": item.album_name,
            }
        )

    return {
        "schema_version": 1,
        "missing_covers": missing,
    }



def _fetch_candidate(cover):

    key = cache_key(
        cover["artist"],
        cover["album"],
    )

    match = search_release(
        cover["artist"],
        cover["album"],
    )

    cover_url = None

    if match:
        cover_url = match.get(
            "cover_url"
        )

    if (
        not cover_url
        and cover["artist"]
        and cover["album"]
    ):
        cover_url = discogs_cover(
            cover["artist"],
            cover["album"],
        )

    return key, {
        **cover,
        "found": bool(match),
        "release": match,
        "release_count": (
            match.get("release_count")
            if match
            else 0
        ),
        "selected_has_cover": (
            match.get(
                "selected_has_cover"
            )
            if match
            else False
        ),
        "cover_found": bool(
            cover_url
        ),
        "cover_url": cover_url,
        "target_file": str(
            cover_target(
                Path(cover["path"])
            )
        ),
    }



def preview_fetch(items):

    cache = load_cover_cache()

    report = analyze_covers(items)

    results = []
    missing = []

    for cover in report["missing_covers"]:

        key = cache_key(
            cover["artist"],
            cover["album"],
        )

        if key in cache:

            results.append(
                {
                    **cache[key],
                    **cover,
                    "target_file": str(
                        cover_target(
                            Path(cover["path"])
                        )
                    ),
                }
            )

        else:

            missing.append(
                cover
            )

    if missing:

        with ThreadPoolExecutor(
            max_workers=4
        ) as executor:

            futures = {
                executor.submit(
                    _fetch_candidate,
                    cover,
                ): cover
                for cover in missing
            }

            total = len(futures)
            current = 0

            for future in as_completed(
                futures
            ):

                current += 1

                key, result = (
                    future.result()
                )

                album = (
                    result["album"]
                    or "unknown"
                )

                status = (
                    "COVER"
                    if result["cover_found"]
                    else (
                        "MATCH"
                        if result["found"]
                        else "MISS"
                    )
                )

                print(
                    f"[{current}/{total}] "
                    f"{album} -> {status}",
                    file=sys.stderr,
                    flush=True,
                )

                cache[key] = result
                results.append(result)
        save_cover_cache(cache)

    return results

def build_download_plan(items):

    cache = load_cover_cache()
    candidates = analyze_covers(items)["missing_covers"]
    plan = []
    seen = set()

    for candidate in candidates:
        key = cache_key(
            candidate["artist"],
            candidate["album"],
        )
        item = cache.get(key)

        if not item or not item["cover_found"] or key in seen:
            continue

        seen.add(key)

        target = cover_target(Path(candidate["path"]))

        plan.append(
            {
                "path": candidate["path"],
                "artist": candidate["artist"],
                "album": candidate["album"],
                "source_url": item["cover_url"],
                "target_file": str(target),
                "action": (
                    "skip"
                    if target.exists()
                    else "create"
                ),
            }
        )

    return {
        "schema_version": 1,
        "downloads": plan,
    }

import requests


def execute_download_plan(items):

    report = build_download_plan(items)

    downloads = report["downloads"]

    results = []

    total = len(downloads)

    for index, item in enumerate(
        downloads,
        start=1,
    ):

        target = Path(
            item["target_file"]
        )

        if target.exists():
            results.append(
                {
                    **item,
                    "success": True,
                    "skipped": True,
                    "error": None,
                }
            )
            continue

        try:

            response = requests.get(
                item["source_url"],
                timeout=30,
            )

            response.raise_for_status()

            with target.open("xb") as cover_file:
                cover_file.write(response.content)

            print(
                f"[{index}/{total}] "
                f"{item['album']} -> OK",
                file=sys.stderr,
                flush=True,
            )

            results.append(
                {
                    **item,
                    "success": True,
                    "skipped": False,
                    "error": None,
                }
            )

        except FileExistsError:
            results.append(
                {
                    **item,
                    "success": True,
                    "skipped": True,
                    "error": None,
                }
            )

        except Exception as exc:

            print(
                f"[{index}/{total}] "
                f"{item['album']} -> ERROR",
                file=sys.stderr,
                flush=True,
            )

            results.append(
                {
                    **item,
                    "success": False,
                    "skipped": False,
                    "error": str(exc),
                }
            )

    return {
        "schema_version": 1,
        "downloads": results,
    }
