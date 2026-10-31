from dontfeartheripper.models import LibraryItem
from dontfeartheripper.stats import build_stats


def item(**kwargs):
    defaults = {
        "path": None,
        "flac_count": 0,
        "has_toc": False,
        "has_cue": False,
        "category": "album",
        "cryptic": False,

        "album_name": None,
        "artist_name": None,
        "disc_number": None,

        "container_directory": False,
        "metadata_source": "unknown",

        "rename_candidate": False,
        "suggested_name": None,
        "rename_collision": False,

        "track_count": 0,
    }

    defaults.update(kwargs)

    return LibraryItem(**defaults)


def test_stats_schema():
    stats = build_stats([])

    assert set(stats.keys()) == {
        "schema_version",
        "albums",
        "compilations",
        "soundtracks",
        "containers",
        "cryptic",
        "toc_files",
        "cue_files",
        "rename_candidates",
        "collisions",
    }


def test_stats_counting():
    stats = build_stats([
        item(category="album", has_toc=True),
        item(category="album"),
        item(category="compilation", cryptic=True),
        item(
            category="soundtrack",
            container_directory=True,
            has_cue=True,
            rename_candidate=True,
            rename_collision=True,
        ),
    ])

    assert stats["albums"] == 2
    assert stats["compilations"] == 1
    assert stats["soundtracks"] == 1

    assert stats["containers"] == 1
    assert stats["cryptic"] == 1

    assert stats["toc_files"] == 1
    assert stats["cue_files"] == 1

    assert stats["rename_candidates"] == 1
    assert stats["collisions"] == 1

    assert stats["schema_version"] == 1
