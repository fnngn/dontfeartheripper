from dataclasses import replace

from .tags2 import TrackMetadata


def first_value(*values):

    for value in values:

        if value is None:
            continue

        if value == "":
            continue

        return value

    return None


def build_recovery_candidate(
    local_metadata,
    container_metadata=None,
    nfo_metadata=None,
    toc_metadata=None,
    musicbrainz_metadata=None,
):

    candidate = replace(
        local_metadata
    )

    candidate.artist = first_value(
        local_metadata.artist,
        nfo_metadata.get("artist")
        if nfo_metadata
        else None,
        container_metadata.get("artist")
        if container_metadata
        else None,
        toc_metadata.get("artist")
        if toc_metadata
        else None,
        musicbrainz_metadata.get("artist")
        if musicbrainz_metadata
        else None,
    )

    candidate.album = first_value(
        local_metadata.album,
        nfo_metadata.get("album")
        if nfo_metadata
        else None,
        container_metadata.get("album")
        if container_metadata
        else None,
        toc_metadata.get("album")
        if toc_metadata
        else None,
        musicbrainz_metadata.get("album")
        if musicbrainz_metadata
        else None,
    )

    candidate.albumartist = first_value(
        local_metadata.albumartist,
        nfo_metadata.get("albumartist")
        if nfo_metadata
        else None,
        container_metadata.get("albumartist")
        if container_metadata
        else None,
        musicbrainz_metadata.get("albumartist")
        if musicbrainz_metadata
        else None,
    )

    candidate.title = first_value(
        local_metadata.title,
        musicbrainz_metadata.get("title")
        if musicbrainz_metadata
        else None,
    )

    return candidate


def metadata_needs_recovery(
    metadata,
):

    return (
        not metadata.artist
        or not metadata.album
    )


def build_repair_operations(
    original,
    candidate,
):

    repairs = []

    if (
        not original.artist
        and candidate.artist
    ):
        repairs.append(
            {
                "field": "artist",
                "old": original.artist,
                "new": candidate.artist,
                "rule": "metadata_recovery",
            }
        )

    if (
        not original.album
        and candidate.album
    ):
        repairs.append(
            {
                "field": "album",
                "old": original.album,
                "new": candidate.album,
                "rule": "metadata_recovery",
            }
        )

    return repairs


RECOVERABLE_FIELDS = (
    "artist",
    "albumartist",
    "album",
    "title",
    "track",
    "disc",
    "genre",
    "year",
)


def build_full_repair_operations(
    original,
    candidate,
):

    repairs = []

    for field in RECOVERABLE_FIELDS:

        old_value = getattr(
            original,
            field,
            None,
        )

        new_value = getattr(
            candidate,
            field,
            None,
        )

        if old_value:
            continue

        if not new_value:
            continue

        repairs.append(
            {
                "field": field,
                "old": old_value,
                "new": new_value,
                "rule":
                    "metadata_recovery",
            }
        )

    return repairs
