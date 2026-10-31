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
    cover_target,
    find_existing_cover,
    has_cover,
)


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
