from pathlib import Path
from tempfile import TemporaryDirectory
import sys

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1] / "src"
    ),
)

from dontfeartheripper.cover import (
    build_download_plan,
    cover_target,
    execute_download_plan,
    find_existing_cover,
    has_cover,
)
from dontfeartheripper.models import LibraryItem


def test_cover_jpg_detected():

    with TemporaryDirectory() as tmp:

        d = Path(tmp)

        (d / "cover.jpg").touch()

        assert has_cover(d)


def test_cover_png_detected():

    with TemporaryDirectory() as tmp:

        d = Path(tmp)

        (d / "cover.PNG").touch()

        assert has_cover(d)


def test_folder_jpg_detected():

    with TemporaryDirectory() as tmp:

        d = Path(tmp)

        (d / "folder.jpg").touch()

        assert has_cover(d)


def test_albumart_detected():

    with TemporaryDirectory() as tmp:

        d = Path(tmp)

        (d / "AlbumArtwork.jpg").touch()

        assert has_cover(d)


def test_artwork_detected():

    with TemporaryDirectory() as tmp:

        d = Path(tmp)

        (d / "TT_OST_Cover.jpg").touch()

        assert has_cover(d)


def test_non_cover_image_ignored():

    with TemporaryDirectory() as tmp:

        d = Path(tmp)

        (d / "wallpaper.jpg").touch()

        assert not has_cover(d)


def test_find_existing_cover_returns_path():

    with TemporaryDirectory() as tmp:

        d = Path(tmp)

        expected = d / "cover.png"

        expected.touch()

        assert find_existing_cover(d) == expected


def test_cover_target_is_cover_jpg():

    with TemporaryDirectory() as tmp:

        d = Path(tmp)

        assert cover_target(d) == (
            d / "cover.jpg"
        )


def test_download_plan_is_limited_to_requested_albums(
    tmp_path,
    monkeypatch,
):
    first_album = tmp_path / "Artist" / "Album"
    first_album.mkdir(parents=True)
    other_album = tmp_path / "Elsewhere" / "Other"
    other_album.mkdir(parents=True)

    cache = {
        "Artist|Album": {
            "cover_found": True,
            "cover_url": "https://example.test/cover.jpg",
        },
        "Other Artist|Other Album": {
            "cover_found": True,
            "cover_url": "https://example.test/other.jpg",
        },
    }
    monkeypatch.setattr(
        "dontfeartheripper.cover.load_cover_cache",
        lambda: cache,
    )

    item = LibraryItem(
        path=first_album,
        flac_count=1,
        has_toc=False,
        has_cue=False,
        category="album",
        cryptic=False,
        artist_name="Artist",
        album_name="Album",
    )

    plan = build_download_plan([item])

    assert len(plan["downloads"]) == 1
    assert plan["downloads"][0]["path"] == str(first_album)
    assert plan["downloads"][0]["target_file"] == str(
        first_album / "cover.jpg"
    )


def test_download_skips_existing_target_without_request(
    tmp_path,
    monkeypatch,
):
    target = tmp_path / "cover.jpg"
    target.touch()

    def unexpected_request(*args, **kwargs):
        raise AssertionError("an existing cover must not be downloaded")

    monkeypatch.setattr(
        "dontfeartheripper.cover.build_download_plan",
        lambda items: {
            "downloads": [
                {
                    "target_file": str(target),
                    "source_url": "https://example.test/cover.jpg",
                    "album": "Album",
                    "action": "skip",
                }
            ]
        },
    )
    monkeypatch.setattr(
        "dontfeartheripper.cover.requests.get",
        unexpected_request,
    )

    report = execute_download_plan([])

    assert report["downloads"][0]["success"]
    assert report["downloads"][0]["skipped"]
