def build_stats(items):
    return {
        "schema_version": 1,
        "albums": sum(
            1 for item in items
            if item.category == "album"
        ),
        "compilations": sum(
            1 for item in items
            if item.category == "compilation"
        ),
        "soundtracks": sum(
            1 for item in items
            if item.category == "soundtrack"
        ),
        "containers": sum(
            1 for item in items
            if item.container_directory
        ),
        "cryptic": sum(
            1 for item in items
            if item.cryptic
        ),
        "toc_files": sum(
            1 for item in items
            if item.has_toc
        ),
        "cue_files": sum(
            1 for item in items
            if item.has_cue
        ),
        "rename_candidates": sum(
            1 for item in items
            if item.rename_candidate
        ),
        "collisions": sum(
            1 for item in items
            if item.rename_collision
        ),
    }
