from pathlib import Path
import sys

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1] / "src"
    ),
)

from dontfeartheripper.tags2 import (
    TrackMetadata,
)

from dontfeartheripper.recovery import (
    build_recovery_candidate,
    metadata_needs_recovery,
)


def test_local_metadata_wins():

    local = TrackMetadata(
        artist="Truckfighters",
        album="Gravity X",
    )

    candidate = build_recovery_candidate(
        local,
        container_metadata={
            "artist": "Wrong",
            "album": "Wrong",
        },
    )

    assert (
        candidate.artist
        == "Truckfighters"
    )

    assert (
        candidate.album
        == "Gravity X"
    )


def test_container_used_when_missing():

    local = TrackMetadata(
        artist=None,
        album=None,
    )

    candidate = build_recovery_candidate(
        local,
        container_metadata={
            "artist": "Truckfighters",
            "album": "Gravity X",
        },
    )

    assert (
        candidate.artist
        == "Truckfighters"
    )

    assert (
        candidate.album
        == "Gravity X"
    )


def test_musicbrainz_is_last_resort():

    local = TrackMetadata()

    candidate = build_recovery_candidate(
        local,
        musicbrainz_metadata={
            "artist": "In Flames",
            "album": "Whoracle",
        },
    )

    assert (
        candidate.artist
        == "In Flames"
    )

    assert (
        candidate.album
        == "Whoracle"
    )


def test_recovery_detection():

    assert metadata_needs_recovery(
        TrackMetadata()
    )

    assert not metadata_needs_recovery(
        TrackMetadata(
            artist="In Flames",
            album="Whoracle",
        )
    )
