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
    detect_backend,
    SUPPORTED_AUDIO_FORMATS,
)


def test_supported_formats():

    assert ".flac" in SUPPORTED_AUDIO_FORMATS
    assert ".mp3" in SUPPORTED_AUDIO_FORMATS
    assert ".wav" in SUPPORTED_AUDIO_FORMATS
    assert ".m4a" in SUPPORTED_AUDIO_FORMATS


def test_backend_detection():

    assert (
        detect_backend(
            Path("foo.flac")
        )
        == "flac"
    )

    assert (
        detect_backend(
            Path("foo.mp3")
        )
        == "mp3"
    )

    assert (
        detect_backend(
            Path("foo.m4a")
        )
        == "mp4"
    )


def test_metadata_model():

    metadata = TrackMetadata(
        artist="Truckfighters",
        album="Gravity X",
    )

    assert (
        metadata.artist
        == "Truckfighters"
    )

    assert (
        metadata.album
        == "Gravity X"
    )
