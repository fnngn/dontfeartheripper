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
    read_tags,
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


def test_read_tags_includes_genre_for_generic_supported_formats(
    tmp_path,
    monkeypatch,
):
    from dontfeartheripper import tags2

    audio_path = tmp_path / "track.wav"
    audio_path.touch()

    class Audio:
        tags = {
            "artist": ["Example Artist"],
            "album": ["Example Album"],
            "title": ["Example Song"],
            "genre": ["Jazz"],
        }

    monkeypatch.setattr(tags2, "MutagenFile", lambda path, easy: Audio())

    metadata = read_tags(audio_path)

    assert metadata.title == "Example Song"
    assert metadata.genre == "Jazz"
