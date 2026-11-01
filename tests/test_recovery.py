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
    build_full_repair_operations,
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


def test_metadata_candidate_repairable():

    local = TrackMetadata(
        artist="",
        album="",
    )

    candidate = build_recovery_candidate(
        local,
        container_metadata={
            "artist": "Truckfighters",
            "album": "Gravity X",
        },
    )

    assert candidate.artist == "Truckfighters"
    assert candidate.album == "Gravity X"


def test_full_metadata_repair_generation():

    original = TrackMetadata()

    candidate = TrackMetadata(
        artist="Truckfighters",
        albumartist="Truckfighters",
        album="Gravity X",
        genre="Stoner Rock",
        year="2005",
    )

    repairs = (
        build_full_repair_operations(
            original,
            candidate,
        )
    )

    fields = {
        repair["field"]
        for repair in repairs
    }

    assert "artist" in fields
    assert "albumartist" in fields
    assert "album" in fields
    assert "genre" in fields
    assert "year" in fields


def test_existing_metadata_not_overwritten():

    original = TrackMetadata(
        artist="Existing",
        album="Existing Album",
    )

    candidate = TrackMetadata(
        artist="Recovered",
        album="Recovered Album",
    )

    repairs = (
        build_full_repair_operations(
            original,
            candidate,
        )
    )

    assert repairs == []


def test_nfo_metadata_preferred_over_container():

    local = TrackMetadata()

    candidate = build_recovery_candidate(
        local,
        container_metadata={
            "artist":
                "Container Artist",
        },
        nfo_metadata={
            "artist":
                "Real Artist",
            "album":
                "Real Album",
        },
    )

    assert (
        candidate.artist
        == "Real Artist"
    )

    assert (
        candidate.album
        == "Real Album"
    )


def test_nfo_album_recovery():

    local = TrackMetadata()

    candidate = build_recovery_candidate(
        local,
        nfo_metadata={
            "album":
                "Cyberpunk 2077 Soundtrack"
        },
    )

    assert (
        candidate.album
        == "Cyberpunk 2077 Soundtrack"
    )
