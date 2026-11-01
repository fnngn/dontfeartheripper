
def test_container_missing_collection_nfo():

    from dontfeartheripper.quality import (
        quality_container_checks,
    )

    issues = quality_container_checks(
        {
            "container_type": "artist_container",
            "container_depth": 0,
        },
        has_collection_nfo=False,
        has_poster=False,
    )

    issue_types = {
        i["type"]
        for i in issues
    }

    assert (
        "container_missing_collection_nfo"
        in issue_types
    )

    assert (
        "container_missing_poster"
        in issue_types
    )


def test_missing_metadata_is_reported_for_none_values():
    from pathlib import Path
    from types import SimpleNamespace

    from dontfeartheripper.quality import analyze_quality

    report = analyze_quality(
        [
            SimpleNamespace(
                path=Path("/music/album"),
                artist_name=None,
                album_name=None,
                metadata_source="flac",
                container_directory=False,
            )
        ]
    )

    assert {
        issue["type"]
        for issue in report["issues"]
    } == {"missing_artist", "missing_album"}
