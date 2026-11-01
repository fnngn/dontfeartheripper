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
        container_metadata.get("artist")
        if container_metadata
        else None,
        nfo_metadata.get("artist")
        if nfo_metadata
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
        container_metadata.get("album")
        if container_metadata
        else None,
        nfo_metadata.get("album")
        if nfo_metadata
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
