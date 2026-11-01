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


def test_scan_reads_metadata_from_supported_audio(
    tmp_path,
    monkeypatch,
):
    from dontfeartheripper.models import LibraryItem
    from dontfeartheripper.scanner import scan_library
    from dontfeartheripper.tags2 import TrackMetadata

    album = tmp_path / "album" / "MP3 Album"
    album.mkdir(parents=True)
    (album / "track01.mp3").touch()
    (album / "track02.mp3").touch()

    monkeypatch.setattr(
        "dontfeartheripper.scanner.read_tags",
        lambda path: TrackMetadata(
            artist="Example Artist",
            albumartist="Example Artist",
            album="Example Album",
            source_format="mp3",
        ),
    )

    items = scan_library(tmp_path)

    assert len(items) == 1
    assert isinstance(items[0], LibraryItem)
    assert items[0].artist_name == "Example Artist"
    assert items[0].album_name == "Example Album"
    assert items[0].metadata_source == "mp3"
    assert items[0].track_count == 2


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
