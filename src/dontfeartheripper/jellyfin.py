import base64
from pathlib import Path
import mimetypes
from typing import Any
from urllib.parse import urljoin

import requests

from .container import (
    find_container_artwork_node,
)
from .progress import ProgressCallback, report_progress
from .progress import OperationCancelled


class JellyfinError(RuntimeError):
    """Raised when a Jellyfin collection operation cannot be completed."""


class JellyfinClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        session: requests.Session | None = None,
        progress: ProgressCallback | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.session = session or requests.Session()
        self.progress = progress
        self.session.headers.update(
            {
                "Authorization": (
                    'MediaBrowser Token="'
                    f'{api_key}", Client="dontfeartheripper", '
                    'Device="dontfeartheripper", '
                    'DeviceId="dontfeartheripper", Version="1.0"'
                ),
                "Accept": "application/json",
            }
        )

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        data: bytes | None = None,
        content_type: str | None = None,
    ) -> requests.Response:
        headers = (
            {"Content-Type": content_type}
            if content_type
            else None
        )
        try:
            response = self.session.request(
                method,
                urljoin(self.base_url, endpoint.lstrip("/")),
                params=params,
                data=data,
                headers=headers,
                timeout=(5, 30),
            )
        except requests.RequestException as exc:
            raise JellyfinError(
                f"Could not contact Jellyfin ({method} {endpoint}): {exc}"
            ) from exc

        if not response.ok:
            raise JellyfinError(
                f"Jellyfin returned HTTP {response.status_code} "
                f"for {method} {endpoint}: {response.text[:500]}"
            )
        return response

    def items(
        self,
        item_type: str | None,
        *,
        parent_id: str | None = None,
    ) -> list[dict[str, Any]]:
        result = []
        start_index = 0
        page_size = 1000

        while True:
            report_progress(
                self.progress,
                f"Loading Jellyfin {item_type or 'collection members'}",
                start_index,
            )
            params: dict[str, Any] = {
                "recursive": "true",
                "fields": "Path",
                "startIndex": start_index,
                "limit": page_size,
            }
            if item_type:
                params["includeItemTypes"] = item_type
            if parent_id:
                params["parentId"] = parent_id

            response = self.request(
                "GET",
                "/Items",
                params=params,
            )
            try:
                payload = response.json()
            except ValueError as exc:
                raise JellyfinError(
                    "Jellyfin returned invalid JSON for its item list."
                ) from exc

            page = payload.get("Items")
            if page is None:
                page = payload.get("items")
            if not isinstance(page, list):
                raise JellyfinError(
                    "Jellyfin item response did not contain an Items list."
                )
            result.extend(page)

            total = payload.get(
                "TotalRecordCount",
                payload.get("totalRecordCount"),
            )
            start_index += len(page)
            report_progress(
                self.progress,
                f"Loaded {len(result)} Jellyfin {item_type or 'items'}",
                min(start_index, total)
                if isinstance(total, int)
                else start_index,
                total if isinstance(total, int) else None,
            )
            if not page or len(page) < page_size:
                break
            if isinstance(total, int) and start_index >= total:
                break

        return result

    def create_collection(
        self,
        name: str,
        item_ids: list[str],
    ) -> str:
        response = self.request(
            "POST",
            "/Collections",
            params={
                "name": name,
                "ids": ",".join(item_ids),
            },
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise JellyfinError(
                f"Jellyfin created {name!r} but returned invalid JSON."
            ) from exc
        collection_id = payload.get("Id", payload.get("id"))
        if not collection_id:
            raise JellyfinError(
                f"Jellyfin created {name!r} without returning a collection ID."
            )
        return str(collection_id)

    def add_items(
        self,
        collection_id: str,
        item_ids: list[str],
    ) -> None:
        if item_ids:
            self.request(
                "POST",
                f"/Collections/{collection_id}/Items",
                params={"ids": ",".join(item_ids)},
            )

    def remove_items(
        self,
        collection_id: str,
        item_ids: list[str],
    ) -> None:
        if item_ids:
            self.request(
                "DELETE",
                f"/Collections/{collection_id}/Items",
                params={"ids": ",".join(item_ids)},
            )

    def upload_primary_image(
        self,
        collection_id: str,
        image_path: Path,
    ) -> None:
        content_type = mimetypes.guess_type(image_path.name)[0]
        if content_type not in ("image/jpeg", "image/png"):
            raise JellyfinError(
                f"Unsupported Jellyfin collection artwork: {image_path}"
            )
        try:
            image_data = image_path.read_bytes()
        except OSError as exc:
            raise JellyfinError(
                f"Could not read collection artwork {image_path}: {exc}"
            ) from exc

        self.request(
            "POST",
            f"/Items/{collection_id}/Images/Primary",
            data=base64.b64encode(image_data),
            content_type=content_type,
        )


def _value(item: dict[str, Any], key: str) -> Any:
    return item.get(key, item.get(key[0].lower() + key[1:]))


def _normalize_path(value: str) -> str:
    return value.replace("\\", "/").rstrip("/").casefold()


def _album_directories(container: dict[str, Any]) -> list[Path]:
    root = Path(container["path"])
    directories = []

    def visit(nodes: list[dict[str, Any]]) -> None:
        for node in nodes:
            if node["type"] == "album":
                directories.append(root / node["path"])
            elif node["type"] == "container":
                visit(node["children"])

    visit(container["children"])
    return directories


def _server_album_paths(
    album_path: Path,
    library_root: Path,
    server_root: str | None,
) -> list[str]:
    if server_root:
        relative = album_path.resolve().relative_to(
            library_root.resolve()
        )
        server_prefix = server_root.rstrip("/\\")
        candidates = [
            f"{server_prefix}/{relative.as_posix()}"
        ]
        for category in ("album", "compilation", "soundtrack"):
            try:
                category_relative = album_path.resolve().relative_to(
                    (library_root / category).resolve()
                )
                candidates.append(
                    f"{server_prefix}/{category_relative.as_posix()}"
                )
                break
            except ValueError:
                continue
        return [_normalize_path(path) for path in candidates]
    return [_normalize_path(str(album_path.resolve()))]


def _match_album_id(
    album_path: Path,
    library_root: Path,
    server_root: str | None,
    server_items: list[dict[str, Any]],
) -> str | None:
    expected_paths = _server_album_paths(
        album_path,
        library_root,
        server_root,
    )
    by_path: dict[str, list[dict[str, Any]]] = {}
    for item in server_items:
        path = _value(item, "Path")
        if path:
            by_path.setdefault(
                _normalize_path(str(path)),
                [],
            ).append(item)

    exact_matches = [
        item
        for expected in expected_paths
        for item in by_path.get(expected, [])
    ]
    exact_ids = {
        str(item_id)
        for item in exact_matches
        if (item_id := _value(item, "Id"))
    }
    if len(exact_ids) == 1:
        return next(iter(exact_ids))
    if exact_ids:
        return None

    category_relative = None
    for category in ("album", "compilation", "soundtrack"):
        category_root = library_root / category
        try:
            category_relative = album_path.resolve().relative_to(
                category_root.resolve()
            )
            break
        except ValueError:
            continue

    if server_root:
        parent_matches = [
            (len(_normalize_path(str(path)).split("/")), item)
            for expected in expected_paths
            for item in server_items
            if (path := _value(item, "Path"))
            and expected.startswith(
                _normalize_path(str(path)) + "/"
            )
        ]
    else:
        suffix = (
            _normalize_path(category_relative.as_posix())
            if category_relative is not None
            else expected_paths[0].lstrip("/")
        )
        suffix_parts = suffix.split("/")
        parent_matches = []
        for item in server_items:
            path = _value(item, "Path")
            if not path:
                continue
            item_parts = _normalize_path(str(path)).split("/")
            for length in range(1, len(suffix_parts)):
                if item_parts[-length:] == suffix_parts[:length]:
                    parent_matches.append((length, item))

    if not parent_matches:
        if server_root:
            return None
        suffix = (
            _normalize_path(category_relative.as_posix())
            if category_relative is not None
            else expected_paths[0].lstrip("/")
        )
        matches = [
            item
            for item in server_items
            if (path := _value(item, "Path"))
            and _normalize_path(str(path)).endswith("/" + suffix)
        ]
        if len(matches) != 1:
            return None
        item_id = _value(matches[0], "Id")
        return str(item_id) if item_id else None

    longest_match = max(length for length, _ in parent_matches)
    matches = [
        item
        for length, item in parent_matches
        if length == longest_match
    ]
    matched_ids = {
        str(item_id)
        for item in matches
        if (item_id := _value(item, "Id"))
    }
    if len(matched_ids) != 1:
        return None
    return next(iter(matched_ids))


def build_jellyfin_collection_plan(
    containers: list[dict[str, Any]],
    client: JellyfinClient,
    library_root: Path,
    server_root: str | None = None,
    progress: ProgressCallback | None = None,
) -> list[dict[str, Any]]:
    names = [Path(container["path"]).name.casefold() for container in containers]
    if len(names) != len(set(names)):
        duplicates = sorted(
            name
            for name in set(names)
            if names.count(name) > 1
        )
        raise JellyfinError(
            "Multiple local containers share a name "
            f"({', '.join(duplicates)}); rename them so Jellyfin "
            "collections can be matched safely."
        )

    albums = client.items("MusicAlbum")
    existing_collections = client.items("BoxSet")
    existing_by_name: dict[str, list[dict[str, Any]]] = {}
    for collection in existing_collections:
        name = _value(collection, "Name")
        if name:
            existing_by_name.setdefault(
                str(name).casefold(),
                [],
            ).append(collection)

    plan = []
    total_containers = len(containers)
    for container_index, container in enumerate(containers, start=1):
        name = Path(container["path"]).name
        item_ids = []
        missing_paths = []
        album_directories = _album_directories(container)
        report_progress(
            progress,
            f"Matching albums: {name}",
            container_index - 1,
            total_containers,
        )
        for album_index, album_path in enumerate(
            album_directories,
            start=1,
        ):
            if album_index == 1 or album_index % 10 == 0:
                report_progress(
                    progress,
                    f"Matching {name}: {album_path.name}",
                    album_index,
                    len(album_directories),
                )
            item_id = _match_album_id(
                album_path,
                library_root,
                server_root,
                albums,
            )
            if item_id:
                item_ids.append(item_id)
            else:
                missing_paths.append(str(album_path))

        matches = existing_by_name.get(name.casefold(), [])
        if len(matches) > 1:
            raise JellyfinError(
                f"More than one Jellyfin collection is named {name!r}; "
                "rename or merge the duplicates before generating."
            )

        existing = matches[0] if matches else None
        collection_id = _value(existing, "Id") if existing else None
        image_tags = (
            _value(existing, "ImageTags")
            if existing
            else {}
        )
        current_ids = set()
        if collection_id:
            current_ids = {
                str(_value(item, "Id"))
                for item in client.items(
                    None,
                    parent_id=str(collection_id),
                )
                if _value(item, "Id")
            }

        artwork = find_container_artwork_node(
            Path(container["path"]),
            container["children"],
            progress,
        )
        desired_ids = set(item_ids)
        plan.append(
            {
                "name": name,
                "container_path": str(container["path"]),
                "collection_id": (
                    str(collection_id)
                    if collection_id
                    else None
                ),
                "has_primary_image": bool(
                    isinstance(image_tags, dict)
                    and (
                        image_tags.get("Primary")
                        or image_tags.get("primary")
                    )
                ),
                "item_ids": sorted(desired_ids),
                "add_ids": sorted(desired_ids - current_ids),
                "remove_ids": sorted(current_ids - desired_ids),
                "missing_paths": missing_paths,
                "artwork_path": str(artwork) if artwork else None,
                "album_count": len(desired_ids) + len(missing_paths),
                "matched_count": len(desired_ids),
            }
        )
        report_progress(
            progress,
            f"Planned {name}",
            container_index,
            total_containers,
        )
    return plan


def apply_jellyfin_collection_plan(
    plan: list[dict[str, Any]],
    client: JellyfinClient,
    progress: ProgressCallback | None = None,
) -> list[dict[str, Any]]:
    results = []
    total = len(plan)
    mutation_started = False
    try:
        for index, entry in enumerate(plan, start=1):
            report_progress(
                progress,
                f"Publishing collection: {entry['name']}",
                index - 1,
                total,
            )
            item_ids = entry["item_ids"]
            if not item_ids:
                results.append(
                    {
                        "name": entry["name"],
                        "status": "skipped",
                        "reason": (
                            "No Jellyfin music albums matched the local paths."
                        ),
                    }
                )
                continue

            collection_id = entry["collection_id"]
            if collection_id:
                if entry["add_ids"]:
                    mutation_started = True
                if entry["remove_ids"]:
                    mutation_started = True
                client.add_items(
                    collection_id,
                    entry["add_ids"],
                )
                if entry["add_ids"]:
                    report_progress(
                        progress,
                        f"Added albums to {entry['name']}",
                        index - 1,
                        total,
                    )
                client.remove_items(
                    collection_id,
                    entry["remove_ids"],
                )
                if entry["remove_ids"]:
                    report_progress(
                        progress,
                        f"Removed stale albums from {entry['name']}",
                        index - 1,
                        total,
                    )
                status = "updated"
            else:
                mutation_started = True
                collection_id = client.create_collection(
                    entry["name"],
                    item_ids,
                )
                report_progress(
                    progress,
                    f"Created collection {entry['name']}",
                    index - 1,
                    total,
                )
                status = "created"

            artwork_path = entry["artwork_path"]
            artwork_uploaded = bool(
                artwork_path
                and not (
                    entry.get("collection_id")
                    and entry.get("has_primary_image")
                )
            )
            if artwork_uploaded:
                mutation_started = True
                client.upload_primary_image(
                    collection_id,
                    Path(artwork_path),
                )
                report_progress(
                    progress,
                    f"Uploaded artwork for {entry['name']}",
                    index - 1,
                    total,
                )

            results.append(
                {
                    "name": entry["name"],
                    "status": status,
                    "collection_id": collection_id,
                    "matched_count": len(item_ids),
                    "missing_paths": entry["missing_paths"],
                    "artwork_uploaded": artwork_uploaded,
                    "existing_artwork_preserved": bool(
                        entry.get("has_primary_image")
                    ),
                }
            )
            report_progress(
                progress,
                f"Published {entry['name']}",
                index,
                total,
            )
    except OperationCancelled as exc:
        if mutation_started:
            raise OperationCancelled(
                "Jellyfin may contain completed changes; inspect its "
                "collections before retrying."
            ) from exc
        raise
    return results


def generate_jellyfin_collections(
    containers: list[dict[str, Any]],
    base_url: str,
    api_key: str,
    library_root: Path,
    *,
    server_root: str | None = None,
    apply: bool = False,
    progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    if not containers:
        return {
            "schema_version": 1,
            "mode": "applied" if apply else "dry_run",
            "collections": [],
            "results": [],
        }

    client = JellyfinClient(
        base_url,
        api_key,
        progress=progress,
    )
    plan = build_jellyfin_collection_plan(
        containers,
        client,
        library_root,
        server_root,
        progress,
    )
    results = (
        apply_jellyfin_collection_plan(plan, client, progress)
        if apply
        else []
    )
    return {
        "schema_version": 1,
        "mode": "applied" if apply else "dry_run",
        "collections": plan,
        "results": results,
    }
