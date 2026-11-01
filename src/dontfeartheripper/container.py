import json

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


def build_container_tree(directory):

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
                        child
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
                            directory
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
                directory
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

    name = container["path"].name.lower()

    children = container["children"]

    child_names = [
        child["name"].lower()
        for child in children
    ]

    if any(
        x.startswith("cd")
        for x in child_names
    ):
        return "disc_container"

    if set(child_names).issubset(
        {
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
    ):
        return "edition_container"

    if (
        "soundtrack" in name
        or "ost" in name
    ):
        return "soundtrack_container"

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
