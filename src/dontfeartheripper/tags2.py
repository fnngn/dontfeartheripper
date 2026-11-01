from dataclasses import dataclass

from mutagen import MutagenError
from mutagen.flac import FLAC
from mutagen.easyid3 import EasyID3
from mutagen.mp4 import MP4

try:
    from mutagen.oggvorbis import OggVorbis
except Exception:
    OggVorbis = None

try:
    from mutagen.oggopus import OggOpus
except Exception:
    OggOpus = None


SUPPORTED_AUDIO_FORMATS = {
    ".flac",
    ".mp3",
    ".m4a",
    ".aac",
    ".ogg",
    ".opus",
    ".wav",
    ".ape",
    ".wv",
}


@dataclass
class TrackMetadata:

    artist: str | None = None
    albumartist: str | None = None

    album: str | None = None
    title: str | None = None

    track: int | None = None
    disc: int | None = None

    genre: str | None = None
    year: str | None = None

    source_format: str = "unknown"


def _first(value):

    if not value:
        return None

    return value[0]


def detect_backend(path):

    suffix = path.suffix.lower()

    if suffix == ".flac":
        return "flac"

    if suffix == ".mp3":
        return "mp3"

    if suffix in (
        ".m4a",
        ".aac",
    ):
        return "mp4"

    if suffix == ".ogg":
        return "ogg"

    if suffix == ".opus":
        return "opus"

    return None


def read_flac(path):

    audio = FLAC(path)

    return TrackMetadata(
        artist=_first(
            audio.get("artist")
        ),
        albumartist=_first(
            audio.get("albumartist")
        ),
        album=_first(
            audio.get("album")
        ),
        title=_first(
            audio.get("title")
        ),
        source_format="flac",
    )


def read_mp3(path):

    audio = EasyID3(path)

    return TrackMetadata(
        artist=_first(
            audio.get("artist")
        ),
        albumartist=_first(
            audio.get("albumartist")
        ),
        album=_first(
            audio.get("album")
        ),
        title=_first(
            audio.get("title")
        ),
        source_format="mp3",
    )


def read_mp4(path):

    audio = MP4(path)

    return TrackMetadata(
        artist=_first(
            audio.get("\xa9ART")
        ),
        album=_first(
            audio.get("\xa9alb")
        ),
        title=_first(
            audio.get("\xa9nam")
        ),
        source_format="mp4",
    )


def read_ogg(path):

    if OggVorbis is None:
        return TrackMetadata()

    audio = OggVorbis(path)

    return TrackMetadata(
        artist=_first(
            audio.get("artist")
        ),
        album=_first(
            audio.get("album")
        ),
        title=_first(
            audio.get("title")
        ),
        source_format="ogg",
    )


def read_opus(path):

    if OggOpus is None:
        return TrackMetadata()

    audio = OggOpus(path)

    return TrackMetadata(
        artist=_first(
            audio.get("artist")
        ),
        album=_first(
            audio.get("album")
        ),
        title=_first(
            audio.get("title")
        ),
        source_format="opus",
    )


def read_tags(path):

    backend = detect_backend(path)

    try:
        if backend == "flac":
            return read_flac(path)

        if backend == "mp3":
            return read_mp3(path)

        if backend == "mp4":
            return read_mp4(path)

        if backend == "ogg":
            return read_ogg(path)

        if backend == "opus":
            return read_opus(path)
    except (MutagenError, OSError, ValueError):
        return TrackMetadata(
            source_format=backend or "unknown"
        )

    return TrackMetadata()


def write_tags(path, metadata):

    backend = detect_backend(path)

    if backend == "flac":

        audio = FLAC(path)

        if metadata.artist:
            audio["artist"] = [
                metadata.artist
            ]

        if metadata.albumartist:
            audio["albumartist"] = [
                metadata.albumartist
            ]

        if metadata.album:
            audio["album"] = [
                metadata.album
            ]

        if metadata.title:
            audio["title"] = [
                metadata.title
            ]

        audio.save()

        return True

    if backend == "mp3":

        audio = EasyID3(path)

        if metadata.artist:
            audio["artist"] = [
                metadata.artist
            ]

        if metadata.albumartist:
            audio["albumartist"] = [
                metadata.albumartist
            ]

        if metadata.album:
            audio["album"] = [
                metadata.album
            ]

        if metadata.title:
            audio["title"] = [
                metadata.title
            ]

        audio.save()

        return True

    return False
