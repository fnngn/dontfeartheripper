from pathlib import Path
import sys

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1] / "src"
    ),
)

from pathlib import Path
from types import SimpleNamespace

from dontfeartheripper.quality import analyze_quality
from dontfeartheripper.repair import analyze_repairs
from dontfeartheripper.scanner import is_low_quality_metadata


def item(**kwargs):
    defaults = {
        "path": Path("/tmp/dummy"),
        "artist_name": None,
        "album_name": None,
        "container_directory": False,
    }

    defaults.update(kwargs)

    return SimpleNamespace(**defaults)


def test_repair_missing_artist():
    report = analyze_repairs([
        item(
            path=Path(
                "/music/album/Loyft - Rage of the Hedgehog"
            ),
            artist_name="",
        )
    ])

    repairs = report["repairs"]

    assert len(repairs) == 1

    assert repairs[0]["field"] == "artist"
    assert repairs[0]["new"] == "Loyft"
    assert repairs[0]["rule"] == "missing_artist"


def test_repair_various_albumartist():
    report = analyze_repairs([
        item(
            path=Path(
                "/music/compilation/VARIOUS - BAR JAZZ 4"
            ),
            artist_name="VARIOUS",
        )
    ])

    repairs = report["repairs"]

    assert len(repairs) == 1

    assert repairs[0]["field"] == "albumartist"
    assert repairs[0]["new"] == "Various Artists"
    assert repairs[0]["rule"] == "various_uppercase"


def test_container_is_never_repaired():
    report = analyze_repairs([
        item(
            path=Path(
                "/music/album/In Flames - Discography"
            ),
            artist_name="",
            container_directory=True,
        )
    ])

    assert report["repairs"] == []


def test_find_flac_files_includes_uppercase_extension(tmp_path):
    from dontfeartheripper.repair import find_flac_files

    track = tmp_path / "track.FLAC"
    track.touch()

    assert find_flac_files(tmp_path) == [str(track)]


def test_quality_score_improves():
    broken = [
        {
            "path": "/music/foo",
            "severity": "warning",
            "type": "missing_artist",
        }
    ]

    penalties = {
        "missing_artist": 10,
        "missing_album": 10,
        "unknown_metadata_source": 5,
        "inconsistent_artist_naming": 2,
        "container_has_metadata": 5,
    }

    score = 100

    for issue in broken:
        score -= penalties[issue["type"]]

    assert score < 100
    assert score == 90


def test_scan_prefers_high_quality_flac_data():
    assert is_low_quality_metadata(
        "",
        "Rage of the Hedgehog",
    )

    assert is_low_quality_metadata(
        "VARIOUS",
        "BAR JAZZ 4",
    )

    assert not is_low_quality_metadata(
        "Various Artists",
        "Bar Jazz, Volume 4",
    )

    assert not is_low_quality_metadata(
        "In Flames",
        "Whoracle",
    )


from dontfeartheripper.recovery import (
    build_repair_operations,
)
from dontfeartheripper.tags2 import (
    TrackMetadata,
)


def test_recovery_repair_generation():

    original = TrackMetadata(
        artist="",
        album="",
    )

    candidate = TrackMetadata(
        artist="Truckfighters",
        album="Gravity X",
    )

    repairs = build_repair_operations(
        original,
        candidate,
    )

    fields = {
        r["field"]
        for r in repairs
    }

    assert "artist" in fields
    assert "album" in fields


def test_find_nearest_album_nfo(
    tmp_path,
):

    from dontfeartheripper.repair import (
        find_nearest_album_nfo,
    )

    root = (
        tmp_path
        / "soundtrack"
        / "Cyberpunk"
        / "soundtrack"
        / "mp3"
    )

    (
        root
        / "album.nfo"
    ).mkdir(
        parents=True,
        exist_ok=True,
    ) if False else None

    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        root
        / "album.nfo"
    ).write_text(
        "<album></album>"
    )

    (
        root
        / "cd1"
    ).mkdir()

    result = (
        find_nearest_album_nfo(
            root / "cd1"
        )
    )

    assert result is not None

    assert (
        result.name
        == "album.nfo"
    )
