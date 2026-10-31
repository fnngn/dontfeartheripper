def analyze_quality(items):
    issues = []

    for item in items:

        if item.artist_name == "":
            issues.append(
                {
                    "path": str(item.path),
                    "severity": "warning",
                    "type": "missing_artist",
                }
            )

        if item.album_name == "":
            issues.append(
                {
                    "path": str(item.path),
                    "severity": "warning",
                    "type": "missing_album",
                }
            )

        if (
            item.metadata_source == "unknown"
            and not item.container_directory
        ):
            issues.append(
                {
                    "path": str(item.path),
                    "severity": "warning",
                    "type": "unknown_metadata_source",
                }
            )

        if (
            item.container_directory
            and (
                item.artist_name
                or item.album_name
            )
        ):
            issues.append(
                {
                    "path": str(item.path),
                    "severity": "warning",
                    "type": "container_has_metadata",
                }
            )

        artist = (item.artist_name or "").strip()

        if artist in (
            "VARIOUS",
            "Various",
        ):
            issues.append(
                {
                    "path": str(item.path),
                    "severity": "warning",
                    "type": "inconsistent_artist_naming",
                }
            )

    penalties = {
        "missing_artist": 10,
        "missing_album": 10,
        "unknown_metadata_source": 5,
        "inconsistent_artist_naming": 2,
        "container_has_metadata": 5,
    }

    score = 100

    for issue in issues:
        score -= penalties.get(
            issue["type"],
            0,
        )

    score = max(score, 0)

    return {
        "schema_version": 1,
        "quality_score": score,
        "issues": issues,
    }
