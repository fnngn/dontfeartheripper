from pathlib import Path
import sys

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1] / "src"
    ),
)

from dontfeartheripper.container import (
    detect_containers,
)


def test_artist_container_detection(
    tmp_path,
):

    (
        tmp_path
        / "album"
        / "Truckfighters"
        / "Gravity X"
    ).mkdir(
        parents=True
    )

    (
        tmp_path
        / "album"
        / "Truckfighters"
        / "Phi"
    ).mkdir(
        parents=True
    )

    (
        tmp_path
        / "album"
        / "Truckfighters"
        / "Gravity X"
        / "track.flac"
    ).touch()

    (
        tmp_path
        / "album"
        / "Truckfighters"
        / "Phi"
        / "track.flac"
    ).touch()

    containers = detect_containers(
        tmp_path
    )

    assert len(containers) == 1

    assert (
        containers[0]["path"].name
        == "Truckfighters"
    )


def test_nested_container_detection(
    tmp_path,
):

    (
        tmp_path
        / "album"
        / "Cyberpunk"
        / "Soundtrack"
        / "CD1"
    ).mkdir(
        parents=True
    )

    (
        tmp_path
        / "album"
        / "Cyberpunk"
        / "Soundtrack"
        / "CD2"
    ).mkdir(
        parents=True
    )

    (
        tmp_path
        / "album"
        / "Cyberpunk"
        / "Soundtrack"
        / "CD1"
        / "track01.flac"
    ).touch()

    (
        tmp_path
        / "album"
        / "Cyberpunk"
        / "Soundtrack"
        / "CD2"
        / "track01.flac"
    ).touch()

    containers = detect_containers(
        tmp_path
    )

    cyberpunk = next(
        c
        for c in containers
        if c["path"].name == "Cyberpunk"
    )

    assert (
        cyberpunk["children"][0]["type"]
        == "container"
    )


def test_multi_level_container_detection(
    tmp_path,
):

    (
        tmp_path
        / "soundtrack"
        / "Game Collection"
        / "Cyberpunk"
        / "Soundtrack"
        / "CD1"
    ).mkdir(
        parents=True
    )

    (
        tmp_path
        / "soundtrack"
        / "Game Collection"
        / "Cyberpunk"
        / "Soundtrack"
        / "CD2"
    ).mkdir(
        parents=True
    )

    (
        tmp_path
        / "soundtrack"
        / "Game Collection"
        / "Cyberpunk"
        / "Soundtrack"
        / "CD1"
        / "track.flac"
    ).touch()

    (
        tmp_path
        / "soundtrack"
        / "Game Collection"
        / "Cyberpunk"
        / "Soundtrack"
        / "CD2"
        / "track.flac"
    ).touch()

    containers = detect_containers(
        tmp_path
    )

    root = next(
        c
        for c in containers
        if c["path"].name
        == "Game Collection"
    )

    assert (
        root["children"][0]["type"]
        == "container"
    )


def test_only_root_container_returned(
    tmp_path,
):

    (
        tmp_path
        / "soundtrack"
        / "Cyberpunk 2077 Bonus Content"
        / "soundtrack"
        / "mp3"
        / "cd1"
    ).mkdir(
        parents=True
    )

    (
        tmp_path
        / "soundtrack"
        / "Cyberpunk 2077 Bonus Content"
        / "soundtrack"
        / "mp3"
        / "cd2"
    ).mkdir(
        parents=True
    )

    (
        tmp_path
        / "soundtrack"
        / "Cyberpunk 2077 Bonus Content"
        / "soundtrack"
        / "mp3"
        / "cd1"
        / "track.flac"
    ).touch()

    (
        tmp_path
        / "soundtrack"
        / "Cyberpunk 2077 Bonus Content"
        / "soundtrack"
        / "mp3"
        / "cd2"
        / "track.flac"
    ).touch()

    containers = detect_containers(
        tmp_path
    )

    assert len(containers) == 1

    assert (
        containers[0]["path"].name
        == "Cyberpunk 2077 Bonus Content"
    )


from dontfeartheripper.container import (
    build_container_metadata,
    build_collection_nfo,
)


def test_artist_container_type(
    tmp_path,
):

    root = (
        tmp_path
        / "album"
        / "Truckfighters"
    )

    (
        root / "Gravity X"
    ).mkdir(
        parents=True
    )

    (
        root / "Phi"
    ).mkdir()

    (
        root / "Gravity X"
        / "track.flac"
    ).touch()

    (
        root / "Phi"
        / "track.flac"
    ).touch()

    container = detect_containers(
        tmp_path
    )[0]

    metadata = build_container_metadata(
        container
    )

    assert (
        metadata["container_type"]
        == "artist_container"
    )


def test_disc_container_type(
    tmp_path,
):

    root = (
        tmp_path
        / "soundtrack"
        / "Cyberpunk"
    )

    (
        root
        / "CD1"
    ).mkdir(
        parents=True
    )

    (
        root
        / "CD2"
    ).mkdir()

    (
        root
        / "CD1"
        / "track.flac"
    ).touch()

    (
        root
        / "CD2"
        / "track.flac"
    ).touch()

    container = detect_containers(
        tmp_path
    )[0]

    metadata = build_container_metadata(
        container
    )

    assert (
        metadata["container_type"]
        == "disc_container"
    )


def test_edition_container_type(
    tmp_path,
):

    root = (
        tmp_path
        / "soundtrack"
        / "Frostpunk"
    )

    (
        root
        / "FLAC"
    ).mkdir(
        parents=True
    )

    (
        root
        / "WAV"
    ).mkdir()

    (
        root
        / "FLAC"
        / "track.flac"
    ).touch()

    (
        root
        / "WAV"
        / "track.wav"
    ).touch()

    container = detect_containers(
        tmp_path
    )[0]

    metadata = build_container_metadata(
        container
    )

    assert (
        metadata["container_type"]
        == "edition_container"
    )


def test_container_metadata_fields(
    tmp_path,
):

    root = (
        tmp_path
        / "album"
        / "Truckfighters"
    )

    (
        root
        / "Gravity X"
    ).mkdir(
        parents=True
    )

    (
        root
        / "Phi"
    ).mkdir()

    (
        root
        / "Gravity X"
        / "track.flac"
    ).touch()

    (
        root
        / "Phi"
        / "track.flac"
    ).touch()

    container = detect_containers(
        tmp_path
    )[0]

    metadata = build_container_metadata(
        container
    )

    assert (
        metadata["schema_version"]
        == 1
    )

    assert (
        metadata["generated_by"]
        == "dontfeartheripper"
    )

    assert (
        metadata["generated_version"]
        == "0.1.3"
    )

    assert (
        metadata["album_count"]
        == 2
    )

    assert (
        metadata["container_depth"]
        == 0
    )


def test_nested_container_depth(
    tmp_path,
):

    (
        tmp_path
        / "soundtrack"
        / "Collection"
        / "Cyberpunk"
        / "CD1"
    ).mkdir(
        parents=True
    )

    (
        tmp_path
        / "soundtrack"
        / "Collection"
        / "Cyberpunk"
        / "CD2"
    ).mkdir()

    (
        tmp_path
        / "soundtrack"
        / "Collection"
        / "Cyberpunk"
        / "CD1"
        / "track.flac"
    ).touch()

    (
        tmp_path
        / "soundtrack"
        / "Collection"
        / "Cyberpunk"
        / "CD2"
        / "track.flac"
    ).touch()

    container = detect_containers(
        tmp_path
    )[0]

    metadata = build_container_metadata(
        container
    )

    assert (
        metadata["container_depth"]
        >= 1
    )


def test_container_id_present(
    tmp_path,
):

    root = (
        tmp_path
        / "album"
        / "Truckfighters"
    )

    (
        root / "Gravity X"
    ).mkdir(
        parents=True
    )

    (
        root / "Phi"
    ).mkdir()

    (
        root / "Gravity X"
        / "track.flac"
    ).touch()

    (
        root / "Phi"
        / "track.flac"
    ).touch()

    container = detect_containers(
        tmp_path
    )[0]

    metadata = build_container_metadata(
        container,
        [container],
    )

    assert metadata["container_id"]

    assert (
        metadata["parent_container"]
        is None
    )


def test_parent_container_reference(
    tmp_path,
):

    (
        tmp_path
        / "soundtrack"
        / "Game Collection"
        / "Cyberpunk"
        / "CD1"
    ).mkdir(
        parents=True
    )

    (
        tmp_path
        / "soundtrack"
        / "Game Collection"
        / "Cyberpunk"
        / "CD2"
    ).mkdir()

    (
        tmp_path
        / "soundtrack"
        / "Game Collection"
        / "Cyberpunk"
        / "CD1"
        / "track.flac"
    ).touch()

    (
        tmp_path
        / "soundtrack"
        / "Game Collection"
        / "Cyberpunk"
        / "CD2"
        / "track.flac"
    ).touch()

    containers = detect_containers(
        tmp_path
    )

    nested = {
        str(c["path"]): build_container_metadata(
            c,
            containers,
        )
        for c in containers
    }

    for metadata in nested.values():

        assert "container_id" in metadata
        assert "parent_container" in metadata


def test_collection_nfo_extended_fields(
    tmp_path,
):

    root = (
        tmp_path
        / "album"
        / "Truckfighters"
    )

    (
        root / "Gravity X"
    ).mkdir(
        parents=True
    )

    (
        root / "Phi"
    ).mkdir()

    (
        root / "Gravity X"
        / "track.flac"
    ).touch()

    (
        root / "Phi"
        / "track.flac"
    ).touch()

    container = detect_containers(
        tmp_path
    )[0]

    xml = build_collection_nfo(
        container
    )

    assert "<uniqueid>" in xml
    assert "<overview>" in xml
    assert "<dateadded>" in xml

    assert (
        "artist_container"
        in xml
    )

    assert (
        "Truckfighters"
        in xml
    )


def test_container_poster_created(
    tmp_path,
):

    from dontfeartheripper.container import (
        write_container_poster,
    )

    root = (
        tmp_path
        / "album"
        / "Truckfighters"
    )

    album = (
        root
        / "Gravity X"
    )

    album.mkdir(
        parents=True
    )

    (
        root
        / "Phi"
    ).mkdir()

    (
        album
        / "track.flac"
    ).touch()

    (
        root
        / "Phi"
        / "track.flac"
    ).touch()

    (
        album
        / "cover.jpg"
    ).write_bytes(
        b"jpg"
    )

    container = detect_containers(
        tmp_path
    )[0]

    target = write_container_poster(
        container
    )

    assert target is not None

    assert (
        root
        / "poster.jpg"
    ).exists()


def test_container_poster_created(
    tmp_path,
):

    from dontfeartheripper.container import (
        write_container_poster,
    )

    root = (
        tmp_path
        / "album"
        / "Truckfighters"
    )

    album = (
        root
        / "Gravity X"
    )

    album.mkdir(
        parents=True
    )

    (
        root
        / "Phi"
    ).mkdir()

    (
        album
        / "track.flac"
    ).touch()

    (
        root
        / "Phi"
        / "track.flac"
    ).touch()

    (
        album
        / "cover.jpg"
    ).write_bytes(
        b"jpg"
    )

    container = detect_containers(
        tmp_path
    )[0]

    target = write_container_poster(
        container
    )

    assert target is not None

    assert (
        root
        / "poster.jpg"
    ).exists()
