import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import tempfile

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
from .progress import (
    OperationCancelled,
    ProgressCallback,
    report_progress,
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



def find_existing_cover(directory, progress=None):

    #
    # Fast path:
    # root directory first
    #

    directory = Path(directory)
    candidates = sorted(directory.iterdir())

    def is_cover(path):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            return False
        stem = path.stem.lower()
        return any(pattern in stem for pattern in COVER_PATTERNS)

    for path in candidates:
        if is_cover(path):
            return path

    visited = 0
    visited_directories = 0

    def raise_walk_error(error):
        raise error

    for current, directories, filenames in os.walk(
        directory,
        onerror=raise_walk_error,
    ):
        visited_directories += 1
        if visited_directories % 100 == 0:
            report_progress(
                progress,
                f"Checking artwork folders: {directory.name}",
                visited_directories,
            )
        directories.sort()
        if Path(current) == directory:
            continue
        for filename in sorted(filenames):
            visited += 1
            if visited == 1 or visited % 500 == 0:
                report_progress(
                    progress,
                    f"Checking artwork files: {directory.name}",
                    visited,
                )
            path = Path(current) / filename
            if is_cover(path):
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


def analyze_covers(
    items,
    progress: ProgressCallback | None = None,
):
    missing = []
    seen = set()
    total = len(items)

    for index, item in enumerate(items, start=1):
        if index == 1 or index % 25 == 0 or index == total:
            report_progress(
                progress,
                f"Checking artwork: {item.path.name}",
                index,
                total,
            )

        if item.container_directory:
            continue

        existing = find_existing_cover(
            item.path,
            progress,
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



def preview_fetch(
    items,
    progress: ProgressCallback | None = None,
):

    cache = load_cover_cache()

    report = analyze_covers(items, progress)

    results = []
    missing = []
    total = len(report["missing_covers"])

    for index, cover in enumerate(
        report["missing_covers"],
        start=1,
    ):

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
            report_progress(
                progress,
                f"Using cached match: {cover['album'] or 'unknown album'}",
                index,
                total,
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

                message = f"Cover lookup: {album} -> {status}"
                report_progress(
                    progress,
                    message,
                    current,
                    len(futures),
                )
                if progress is None:
                    print(
                        f"[{current}/{len(futures)}] "
                        f"{album} -> {status}",
                        file=sys.stderr,
                        flush=True,
                    )

                cache[key] = result
                results.append(result)
        save_cover_cache(cache)

    return results

def build_download_plan(
    items,
    progress: ProgressCallback | None = None,
):

    cache = load_cover_cache()
    candidates = analyze_covers(items, progress)["missing_covers"]
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


def execute_download_plan(
    items,
    progress: ProgressCallback | None = None,
):

    report = (
        build_download_plan(items)
        if progress is None
        else build_download_plan(items, progress)
    )

    downloads = report["downloads"]

    results = []

    total = len(downloads)
    report_progress(progress, "Preparing cover downloads", 0, total)

    for index, item in enumerate(
        downloads,
        start=1,
    ):

        target = Path(
            item["target_file"]
        )

        if target.exists():
            report_progress(
                progress,
                f"Keeping existing cover: {item['album']}",
                index,
                total,
            )
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
            temporary_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    dir=target.parent,
                    prefix=f".{target.name}.",
                    delete=False,
                ) as cover_file:
                    temporary_path = Path(cover_file.name)
                    cover_file.write(response.content)
                    cover_file.flush()
                    os.fsync(cover_file.fileno())
                os.link(temporary_path, target)
            finally:
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)

            if progress is None:
                print(
                    f"[{index}/{total}] "
                    f"{item['album']} -> OK",
                    file=sys.stderr,
                    flush=True,
                )
            report_progress(
                progress,
                f"Downloaded cover: {item['album']}",
                index,
                total,
            )

            results.append(
                {
                    **item,
                    "success": True,
                    "skipped": False,
                    "error": None,
                }
            )

        except OperationCancelled:
            raise

        except FileExistsError:
            report_progress(
                progress,
                f"Keeping existing cover: {item['album']}",
                index,
                total,
            )
            results.append(
                {
                    **item,
                    "success": True,
                    "skipped": True,
                    "error": None,
                }
            )

        except Exception as exc:

            if progress is None:
                print(
                    f"[{index}/{total}] "
                    f"{item['album']} -> ERROR",
                    file=sys.stderr,
                    flush=True,
                )
            report_progress(
                progress,
                f"Cover download failed: {item['album']}",
                index,
                total,
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
