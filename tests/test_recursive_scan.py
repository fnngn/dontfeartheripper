from dontfeartheripper.scanner import scan_library


def test_recursive_album_discovery(tmp_path):

    album = (
        tmp_path
        / "album"
        / "Artist"
        / "Test Album"
    )

    album.mkdir(
        parents=True
    )

    (
        album / "track01.mp3"
    ).touch()

    items = scan_library(
        tmp_path
    )

    assert len(items) == 1

    assert (
        items[0].path.name
        == "Test Album"
    )


def test_mp3_album_detected(tmp_path):

    album = (
        tmp_path
        / "album"
        / "MP3 Album"
    )

    album.mkdir(
        parents=True
    )

    (
        album / "track01.mp3"
    ).touch()

    items = scan_library(
        tmp_path
    )

    assert len(items) == 1


def test_wav_album_detected(tmp_path):

    album = (
        tmp_path
        / "album"
        / "WAV Album"
    )

    album.mkdir(
        parents=True
    )

    (
        album / "track01.wav"
    ).touch()

    items = scan_library(
        tmp_path
    )

    assert len(items) == 1


def test_container_children_discovered(tmp_path):

    root = (
        tmp_path
        / "album"
        / "Alan Parsons Project"
    )

    (
        root
        / "Gaudi"
    ).mkdir(
        parents=True
    )

    (
        root
        / "Pyramid"
    ).mkdir(
        parents=True
    )

    (
        root
        / "Gaudi"
        / "track01.flac"
    ).touch()

    (
        root
        / "Pyramid"
        / "track01.flac"
    ).touch()

    items = scan_library(
        tmp_path
    )

    names = {
        item.path.name
        for item in items
    }

    assert "Gaudi" in names
    assert "Pyramid" in names
    assert len(items) == 2
