from dontfeartheripper.library_db import (
    invalidate_library,
    load_library,
)
from dontfeartheripper.library_search import search_library
from dontfeartheripper.models import LibraryItem
from dontfeartheripper.tags2 import TrackMetadata


def _item(album_path, **values):
    defaults = {
        "path": album_path,
        "flac_count": 0,
        "has_toc": False,
        "has_cue": False,
        "category": "album",
        "cryptic": False,
        "album_name": "Jazz Album",
        "artist_name": "Jazz Artist",
    }
    defaults.update(values)
    return LibraryItem(**defaults)


def test_search_indexes_tracks_and_collections_only_once(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "music"
    album_path = root / "album" / "Jazz Artist" / "Jazz Album"
    album_path.mkdir(parents=True)
    (album_path / "track.mp3").touch()
    collection_path = root / "album" / "Jazz Collection"
    monkeypatch.setenv(
        "DFTR_DATABASE_PATH",
        str(tmp_path / "index.sqlite3"),
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_db.scan_library",
        lambda root, progress: [_item(album_path)],
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_db.detect_containers",
        lambda root, progress: [
            {
                "path": collection_path,
                "children": [{"type": "album"}],
            }
        ],
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_db.read_tags",
        lambda path: TrackMetadata(
            artist="Jazz Artist",
            album="Jazz Album",
            title="Jazz at Night",
            genre="Jazz",
        ),
    )
    updates = []

    results = search_library(
        root,
        "jazz",
        lambda message, current, total: updates.append(
            (message, current, total)
        ),
    )

    assert any(result.startswith("SONG") for result in results)
    assert any(result.startswith("ARTIST") for result in results)
    assert any(result.startswith("ALBUM") for result in results)
    assert any(result.startswith("GENRE") for result in results)
    assert any(result.startswith("COLLECTION") for result in results)
    assert updates[-1][0] == f"Search complete · {len(results)} matches"

    monkeypatch.setattr(
        "dontfeartheripper.library_db.scan_library",
        lambda *args: (_ for _ in ()).throw(
            AssertionError("an indexed search must not rescan the library")
        ),
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_db.read_tags",
        lambda *args: (_ for _ in ()).throw(
            AssertionError("an indexed search must not reread track tags")
        ),
    )
    assert search_library(root, "night") == [
        "SONG  Jazz Artist — Jazz at Night  [Jazz Album]"
    ]


def test_search_uses_filename_when_track_title_is_missing(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "music"
    album_path = root / "album" / "Artist" / "Album"
    album_path.mkdir(parents=True)
    (album_path / "Midnight Train.mp3").touch()
    monkeypatch.setenv(
        "DFTR_DATABASE_PATH",
        str(tmp_path / "index.sqlite3"),
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_db.scan_library",
        lambda root, progress: [
            _item(
                album_path,
                album_name="Album",
                artist_name="Artist",
            )
        ],
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_db.detect_containers",
        lambda root, progress: [],
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_db.read_tags",
        lambda path: TrackMetadata(),
    )

    assert search_library(root, "midnight") == [
        "SONG  Artist — Midnight Train  [Album]"
    ]


def test_refresh_replaces_cached_library_items(tmp_path, monkeypatch):
    root = tmp_path / "music"
    root.mkdir()
    monkeypatch.setenv(
        "DFTR_DATABASE_PATH",
        str(tmp_path / "index.sqlite3"),
    )
    items = [_item(root / "album", album_name="First")]
    monkeypatch.setattr(
        "dontfeartheripper.library_db.scan_library",
        lambda root, progress: items,
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_db.detect_containers",
        lambda root, progress: [],
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_db.read_tags",
        lambda path: TrackMetadata(),
    )

    assert load_library(root)[0].album_name == "First"
    items[:] = [_item(root / "album", album_name="Updated")]

    assert load_library(root)[0].album_name == "First"
    assert load_library(root, refresh=True)[0].album_name == "Updated"


def test_interrupted_refresh_keeps_the_previous_complete_index(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "music"
    root.mkdir()
    monkeypatch.setenv(
        "DFTR_DATABASE_PATH",
        str(tmp_path / "index.sqlite3"),
    )
    items = [_item(root / "album", album_name="First")]
    monkeypatch.setattr(
        "dontfeartheripper.library_db.scan_library",
        lambda root, progress: items,
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_db.detect_containers",
        lambda root, progress: [],
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_db.read_tags",
        lambda path: TrackMetadata(),
    )
    load_library(root)
    items[:] = [_item(root / "album", album_name="Incomplete")]

    def interrupt_refresh(message, current, total):
        if message.startswith("Search index ready"):
            raise RuntimeError("interrupted refresh")

    try:
        load_library(root, interrupt_refresh, refresh=True)
    except RuntimeError as exc:
        assert str(exc) == "interrupted refresh"
    else:
        raise AssertionError("the refresh should be interrupted")

    assert load_library(root)[0].album_name == "First"
    assert search_library(root, "first")
    assert not search_library(root, "incomplete")


def test_invalidated_database_rebuilds_on_next_load(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "music"
    root.mkdir()
    monkeypatch.setenv(
        "DFTR_DATABASE_PATH",
        str(tmp_path / "index.sqlite3"),
    )
    items = [_item(root / "album", album_name="First")]
    monkeypatch.setattr(
        "dontfeartheripper.library_db.scan_library",
        lambda root, progress: items,
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_db.detect_containers",
        lambda root, progress: [],
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_db.read_tags",
        lambda path: TrackMetadata(),
    )
    load_library(root)
    items[:] = [_item(root / "album", album_name="Updated")]
    invalidate_library(root)

    assert load_library(root)[0].album_name == "Updated"
