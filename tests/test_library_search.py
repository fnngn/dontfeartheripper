from dontfeartheripper.library_search import search_library
from dontfeartheripper.models import LibraryItem
from dontfeartheripper.tags2 import TrackMetadata


def test_search_finds_song_artist_album_genre_and_collection(
    tmp_path,
    monkeypatch,
):
    album_path = tmp_path / "album" / "Jazz Artist" / "Jazz Album"
    album_path.mkdir(parents=True)
    (album_path / "track.mp3").touch()
    item = LibraryItem(
        path=album_path,
        flac_count=0,
        has_toc=False,
        has_cue=False,
        category="album",
        cryptic=False,
        album_name="Jazz Album",
        artist_name="Jazz Artist",
    )
    collection_path = tmp_path / "album" / "Jazz Collection"
    monkeypatch.setattr(
        "dontfeartheripper.library_search.detect_containers",
        lambda root, progress: [
            {
                "path": collection_path,
                "children": [{"type": "album"}],
            }
        ],
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_search.read_tags",
        lambda path: TrackMetadata(
            artist="Jazz Artist",
            album="Jazz Album",
            title="Jazz at Night",
            genre="Jazz",
        ),
    )
    updates = []

    results = search_library(
        tmp_path,
        [item],
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


def test_search_falls_back_to_audio_filename(tmp_path, monkeypatch):
    album_path = tmp_path / "album" / "Artist" / "Album"
    album_path.mkdir(parents=True)
    (album_path / "Midnight Train.mp3").touch()
    item = LibraryItem(
        path=album_path,
        flac_count=0,
        has_toc=False,
        has_cue=False,
        category="album",
        cryptic=False,
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_search.detect_containers",
        lambda root, progress: [],
    )
    monkeypatch.setattr(
        "dontfeartheripper.library_search.read_tags",
        lambda path: TrackMetadata(),
    )

    results = search_library(tmp_path, [item], "midnight")

    assert results == ["SONG  Artist — Midnight Train  [Album]"]
