
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
