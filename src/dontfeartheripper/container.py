import json
import xml.etree.ElementTree as ET

from pathlib import Path


CONTAINER_FILENAME = ".dftr-container.json"

AUDIO_EXTENSIONS = {
    ".flac",
    ".mp3",
    ".m4a",
    ".aac",
    ".ogg",
    ".opus",
    ".wav",
    ".ape",
    ".wv",
}


def has_audio(directory):

    for item in directory.rglob("*"):

        if (
            item.is_file()
            and item.suffix.lower()
            in AUDIO_EXTENSIONS
        ):
            return True

    return False


def build_container_tree(
    directory,
    root=None,
):

    if root is None:
        root = directory

    subdirs = [
        p
        for p in sorted(directory.iterdir())
        if p.is_dir()
    ]

    children = []

    for child in subdirs:

        nested_subdirs = [
            p
            for p in child.iterdir()
            if p.is_dir()
        ]

        audio = has_audio(child)

        nested_audio_dirs = [
            d
            for d in nested_subdirs
            if has_audio(d)
        ]

        if nested_audio_dirs:

            children.append(
                {
                    "type": "container",
                    "name": child.name,
                    "children": build_container_tree(
                        child,
                        root,
                    ),
                }
            )

        elif audio:

            children.append(
                {
                    "type": "album",
                    "name": child.name,
                    "path": str(
                        child.relative_to(
                            root
                        )
                    ),
                }
            )

    return children




def count_album_nodes(children):

    total = 0

    for child in children:

        if child["type"] == "album":
            total += 1

        elif child["type"] == "container":
            total += count_album_nodes(
                child["children"]
            )

    return total

def detect_containers(root):

    containers = []

    for category in (
        "album",
        "compilation",
        "soundtrack",
    ):

        base = root / category

        if not base.exists():
            continue

        for directory in base.rglob("*"):

            if not directory.is_dir():
                continue

            tree = build_container_tree(
                directory,
                directory,
            )

            album_count = count_album_nodes(
                tree
            )

            if album_count < 2:
                continue

            containers.append(
                {
                    "path": directory,
                    "children": tree,
                }
            )

    root_containers = []

    for container in containers:

        if is_nested_container(
            container["path"],
            containers,
        ):
            continue

        root_containers.append(
            container
        )

    return root_containers




def is_nested_container(candidate, containers):

    candidate = candidate.resolve()

    for other in containers:

        other_path = other["path"].resolve()

        if other_path == candidate:
            continue

        try:

            candidate.relative_to(
                other_path
            )

            return True

        except ValueError:

            pass

    return False







CONTAINER_SCHEMA_VERSION = 1
CONTAINER_GENERATOR = "dontfeartheripper"
CONTAINER_GENERATOR_VERSION = "0.1.3"


def container_depth(children):

    depth = 0

    for child in children:

        if child["type"] == "container":

            depth = max(
                depth,
                1 + container_depth(
                    child["children"]
                )
            )

    return depth



def classify_container(container):

    name = (
        container["path"]
        .name
        .lower()
        .strip()
    )

    children = container["children"]

    child_names = [
        child["name"].lower()
        for child in children
    ]

    DISC_NAMES = {
        "cd1",
        "cd2",
        "cd3",
        "cd4",
        "disc1",
        "disc2",
        "disc3",
        "disc4",
        "disc 1",
        "disc 2",
        "disc 3",
        "disc 4",
    }

    FORMAT_NAMES = {
        "flac",
        "wav",
        "mp3",
        "aac",
        "ogg",
        "opus",
        "m4a",
        "ape",
        "wv",
    }

    ALBUM_EDITION_HINTS = (
        "super deluxe",
        "deluxe",
        "expanded edition",
        "collector",
        "anniversary edition",
        "box set",
    )

    #
    # Disc container
    #

    if any(
        disc_name in child_names
        for disc_name in DISC_NAMES
    ):
        return "disc_container"

    #
    # Format container
    #

    if (
        child_names
        and set(child_names).issubset(
            FORMAT_NAMES
        )
    ):
        return "format_container"

    #
    # Album container
    #

    if any(
        hint in name
        for hint in ALBUM_EDITION_HINTS
    ):
        return "album_container"

    #
    # Soundtrack container
    #

    if (
        "soundtrack" in name
        or "ost" in name
    ):
        return "soundtrack_container"

    #
    # Artist container
    #

    album_count = count_album_nodes(
        children
    )

    if album_count >= 2:
        return "artist_container"

    return "generic_container"

def make_container_id(path):

    return (
        str(path)
        .lower()
        .replace("/", "-")
        .replace(" ", "-")
    )


def find_parent_container(
    container,
    containers,
):

    current = container["path"]

    parent = None

    parent_len = -1

    for other in containers:

        other_path = other["path"]

        if other_path == current:
            continue

        try:

            current.relative_to(
                other_path
            )

            length = len(
                other_path.parts
            )

            if length > parent_len:

                parent = make_container_id(
                    other_path
                )

                parent_len = length

        except ValueError:

            pass

    return parent


def build_container_metadata(
    container,
    containers=None,
):

    container_type = classify_container(
        container
    )

    return {
        "schema_version": (
            CONTAINER_SCHEMA_VERSION
        ),
        "generated_by": (
            CONTAINER_GENERATOR
        ),
        "generated_version": (
            CONTAINER_GENERATOR_VERSION
        ),
        "container_id": make_container_id(
            container["path"]
        ),
        "parent_container":
            (
                find_parent_container(
                    container,
                    containers or [],
                )
            ),
        "container_type": container_type,
        "name": container["path"].name,
        "album_count": count_album_nodes(
            container["children"]
        ),
        "container_depth": container_depth(
            container["children"]
        ),
        "children": container["children"],
    }


def write_container_metadata(
    container,
):

    target = (
        container["path"]
        / CONTAINER_FILENAME
    )

    metadata = build_container_metadata(
        container,
        [container],
    )

    target.write_text(
        json.dumps(
            metadata,
            indent=2,
        )
    )

    return target




import shutil
from .cover import find_existing_cover



def find_container_artwork_node(
    container_root,
    nodes,
):

    for node in nodes:

        if node["type"] == "album":

            album_dir = (
                container_root
                / node["path"]
            )

            cover = find_existing_cover(
                album_dir
            )

            if cover:
                return cover

        elif (
            node["type"]
            == "container"
        ):

            cover = (
                find_container_artwork_node(
                    container_root,
                    node["children"],
                )
            )

            if cover:
                return cover

    return None

def write_container_poster(
    container,
):

    source = find_container_artwork_node(
        container["path"],
        container["children"],
    )

    if source is None:
        return None

    extension = (
        ".png"
        if source.suffix.lower() == ".png"
        else ".jpg"
    )
    target = container["path"] / f"poster{extension}"

    shutil.copy2(
        source,
        target,
    )

    return target

def build_collection_nfo(container):

    from datetime import date

    metadata = build_container_metadata(
        container
    )

    overview = (
        "Automatically generated by "
        "dontfeartheripper. "
        f"Container type: "
        f"{metadata['container_type']}. "
        f"Albums: "
        f"{metadata['album_count']}."
    )

    root = ET.Element("collection")
    values = {
        "title": metadata["name"],
        "uniqueid": metadata["container_id"],
        "overview": overview,
        "type": metadata["container_type"],
        "albumcount": str(metadata["album_count"]),
        "depth": str(metadata["container_depth"]),
        "dateadded": date.today().isoformat(),
    }

    for tag, value in values.items():
        ET.SubElement(root, tag).text = value

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + ET.tostring(root, encoding="unicode")
        + "\n"
    )


def write_collection_nfo(
    container,
):

    target = (
        container["path"]
        / "collection.nfo"
    )

    target.write_text(
        build_collection_nfo(
            container
        ),
        encoding="utf-8",
    )

    return target


def load_container_metadata(
    directory,
):

    metadata_file = (
        Path(directory)
        / CONTAINER_FILENAME
    )

    if not metadata_file.exists():
        return None

    try:

        return json.loads(
            metadata_file.read_text()
        )

    except Exception:

        return None


def resolve_container_context(
    path,
):

    current = Path(path).resolve()

    for parent in (
        current,
        *current.parents,
    ):

        metadata = load_container_metadata(
            parent
        )

        if metadata:
            return metadata

    return None
