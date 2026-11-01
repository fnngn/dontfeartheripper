from dataclasses import asdict
import json
import os
from pathlib import Path
import sqlite3
import time

from .container import AUDIO_EXTENSIONS as CONTAINER_AUDIO_EXTENSIONS
from .container import count_album_nodes, detect_containers
from .models import LibraryItem
from .progress import ProgressCallback, report_progress
from .scanner import scan_library
from .tags2 import read_tags


DATABASE_VERSION = 1


def database_path() -> Path:
    override = os.environ.get("DFTR_DATABASE_PATH")
    if override:
        return Path(override).expanduser()
    cache_root = Path(
        os.environ.get(
            "XDG_CACHE_HOME",
            Path.home() / ".cache",
        )
    ).expanduser()
    return cache_root / "dontfeartheripper" / "library.sqlite3"


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix":
        path.parent.chmod(0o700)
    connection = sqlite3.connect(path, timeout=60)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 60000")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    connection.execute("PRAGMA temp_store = MEMORY")
    return connection


def _initialize(connection: sqlite3.Connection) -> bool:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS libraries (
            root TEXT PRIMARY KEY,
            indexed_at REAL NOT NULL,
            database_version INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS albums (
            root TEXT NOT NULL,
            path TEXT NOT NULL,
            item_json TEXT NOT NULL,
            PRIMARY KEY (root, path)
        );
        CREATE TABLE IF NOT EXISTS search_entries (
            id INTEGER PRIMARY KEY,
            root TEXT NOT NULL,
            kind TEXT NOT NULL,
            entity_path TEXT NOT NULL,
            display TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            artist TEXT NOT NULL DEFAULT '',
            album TEXT NOT NULL DEFAULT '',
            genre TEXT NOT NULL DEFAULT '',
            collection TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS search_entries_root_kind
            ON search_entries (root, kind);
        """
    )
    try:
        connection.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS search_fts USING fts5(
                root UNINDEXED,
                kind UNINDEXED,
                entity_path UNINDEXED,
                display,
                title,
                artist,
                album,
                genre,
                collection,
                tokenize='trigram'
            )
            """
        )
    except sqlite3.OperationalError:
        return False
    return True


def _serialize_item(item: LibraryItem) -> str:
    serialized = asdict(item)
    serialized["path"] = str(item.path)
    return json.dumps(serialized)


def _deserialize_item(value: str) -> LibraryItem:
    item = json.loads(value)
    item["path"] = Path(item["path"])
    return LibraryItem(**item)


def _rebuild(
    connection: sqlite3.Connection,
    root: Path,
    progress: ProgressCallback | None,
    fts_enabled: bool,
) -> list[LibraryItem]:
    root_key = str(root.resolve())
    report_progress(progress, "Scanning music folders to build the index")
    items = scan_library(root, progress)
    connection.execute("DELETE FROM albums WHERE root = ?", (root_key,))
    connection.execute("DELETE FROM search_entries WHERE root = ?", (root_key,))
    if fts_enabled:
        connection.execute("DELETE FROM search_fts WHERE root = ?", (root_key,))

    connection.executemany(
        "INSERT INTO albums (root, path, item_json) VALUES (?, ?, ?)",
        (
            (root_key, str(item.path), _serialize_item(item))
            for item in items
        ),
    )

    entry_sql = """
        INSERT INTO search_entries
            (root, kind, entity_path, display, title, artist, album, genre,
             collection)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    entry_batch = []

    def add_entry(
        kind,
        entity_path,
        display,
        *,
        title="",
        artist="",
        album="",
        genre="",
        collection="",
    ):
        entry_batch.append(
            (
                root_key,
                kind,
                entity_path,
                display,
                title,
                artist,
                album,
                genre,
                collection,
            )
        )
        if len(entry_batch) >= 512:
            flush_entries()

    def flush_entries():
        if not entry_batch:
            return
        connection.executemany(entry_sql, entry_batch)
        entry_batch.clear()

    for item in items:
        artist = item.artist_name or item.path.parent.name
        album = item.album_name or item.path.name
        add_entry(
            "album",
            str(item.path),
            f"ALBUM  {artist} — {album}  [{item.category}]",
            artist=artist,
            album=album,
            genre=item.genre or "",
        )
        add_entry(
            "artist",
            artist.casefold(),
            f"ARTIST  {artist}",
            artist=artist,
        )
        if item.genre:
            add_entry(
                "genre",
                f"{item.genre.casefold()}|{item.path}",
                f"GENRE  {item.genre} — {artist} / {album}",
                artist=artist,
                album=album,
                genre=item.genre,
            )

    track_files = [
        (item, audio_path)
        for item in items
        if not item.container_directory and item.path.is_dir()
        for audio_path in sorted(item.path.iterdir())
        if (
            audio_path.is_file()
            and audio_path.suffix.lower() in CONTAINER_AUDIO_EXTENSIONS
        )
    ]
    total_tracks = len(track_files)
    report_progress(
        progress,
        "Reading track details for the search index",
        0,
        total_tracks,
    )
    for index, (item, audio_path) in enumerate(track_files, start=1):
        if index == 1 or index % 20 == 0 or index == total_tracks:
            report_progress(
                progress,
                f"Indexing track {index}/{total_tracks}: {audio_path.name}",
                index,
                total_tracks,
            )
        metadata = read_tags(audio_path)
        artist = (
            metadata.artist
            or metadata.albumartist
            or item.artist_name
            or item.path.parent.name
        )
        album = metadata.album or item.album_name or item.path.name
        title = metadata.title or audio_path.stem
        genre = metadata.genre or item.genre or ""
        add_entry(
            "song",
            str(audio_path),
            f"SONG  {artist} — {title}  [{album}]",
            title=title,
            artist=artist,
            album=album,
            genre=genre,
        )
        if genre and genre.casefold() != (item.genre or "").casefold():
            add_entry(
                "genre",
                f"{genre.casefold()}|{item.path}",
                f"GENRE  {genre} — {artist} / {album}",
                artist=artist,
                album=album,
                genre=genre,
            )

    report_progress(progress, "Indexing music collections")
    for collection in detect_containers(root, progress):
        name = Path(collection["path"]).name
        album_count = count_album_nodes(collection["children"])
        add_entry(
            "collection",
            str(collection["path"]),
            f"COLLECTION  {name} · {album_count} albums",
            collection=name,
        )

    flush_entries()
    if fts_enabled:
        connection.execute(
            """
            INSERT INTO search_fts
                (root, kind, entity_path, display, title, artist, album, genre,
                 collection)
            SELECT root, kind, entity_path, display, title, artist, album,
                   genre, collection
            FROM search_entries
            WHERE root = ?
            """,
            (root_key,),
        )
    connection.execute(
        """
        INSERT INTO libraries (root, indexed_at, database_version)
        VALUES (?, ?, ?)
        ON CONFLICT(root) DO UPDATE SET
            indexed_at = excluded.indexed_at,
            database_version = excluded.database_version
        """,
        (root_key, time.time(), DATABASE_VERSION),
    )
    report_progress(
        progress,
        f"Search index ready · {len(items)} albums, {total_tracks} tracks",
        total_tracks,
        total_tracks,
    )
    return items


def load_library(
    root: Path,
    progress: ProgressCallback | None = None,
    *,
    refresh: bool = False,
) -> list[LibraryItem]:
    root = Path(root).expanduser().resolve()
    path = database_path()
    connection = _connect(path)
    try:
        fts_enabled = _initialize(connection)
        root_key = str(root)
        indexed = connection.execute(
            """
            SELECT database_version FROM libraries WHERE root = ?
            """,
            (root_key,),
        ).fetchone()
        if refresh or indexed is None or indexed["database_version"] != DATABASE_VERSION:
            connection.execute("BEGIN IMMEDIATE")
            try:
                if not refresh:
                    indexed = connection.execute(
                        """
                        SELECT database_version FROM libraries WHERE root = ?
                        """,
                        (root_key,),
                    ).fetchone()
                    if (
                        indexed is not None
                        and indexed["database_version"] == DATABASE_VERSION
                    ):
                        rows = connection.execute(
                            """
                            SELECT item_json FROM albums
                            WHERE root = ? ORDER BY path
                            """,
                            (root_key,),
                        ).fetchall()
                        connection.commit()
                        report_progress(
                            progress,
                            f"Loaded {len(rows)} albums from the local index",
                        )
                        return [
                            _deserialize_item(row["item_json"])
                            for row in rows
                        ]
                items = _rebuild(
                    connection,
                    root,
                    progress,
                    fts_enabled,
                )
                connection.commit()
                return items
            except BaseException:
                connection.rollback()
                raise

        rows = connection.execute(
            "SELECT item_json FROM albums WHERE root = ? ORDER BY path",
            (root_key,),
        ).fetchall()
        report_progress(progress, f"Loaded {len(rows)} albums from the local index")
        return [_deserialize_item(row["item_json"]) for row in rows]
    finally:
        connection.close()


def search_index(
    root: Path,
    query: str,
    progress: ProgressCallback | None = None,
) -> list[str]:
    needle = query.strip()
    if not needle:
        return []
    root_key = str(Path(root).expanduser().resolve())
    path = database_path()
    connection = _connect(path)
    try:
        fts_enabled = _initialize(connection)
        indexed = connection.execute(
            """
            SELECT 1 FROM libraries WHERE root = ? AND database_version = ?
            """,
            (root_key, DATABASE_VERSION),
        ).fetchone()
        if indexed is None:
            connection.close()
            load_library(root, progress)
            connection = _connect(path)
            fts_enabled = _initialize(connection)

        report_progress(progress, "Searching the local music index")
        if fts_enabled and len(needle) >= 3:
            match_query = '"' + needle.replace('"', '""') + '"'
            rows = connection.execute(
                """
                SELECT kind, entity_path, display
                FROM search_fts
                WHERE root = ? AND search_fts MATCH ?
                ORDER BY kind, display COLLATE NOCASE
                """,
                (root_key, match_query),
            ).fetchall()
        else:
            pattern = "%" + needle.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            rows = connection.execute(
                """
                SELECT kind, entity_path, display
                FROM search_entries
                WHERE root = ? AND (
                    display LIKE ? ESCAPE '\\' COLLATE NOCASE OR
                    title LIKE ? ESCAPE '\\' COLLATE NOCASE OR
                    artist LIKE ? ESCAPE '\\' COLLATE NOCASE OR
                    album LIKE ? ESCAPE '\\' COLLATE NOCASE OR
                    genre LIKE ? ESCAPE '\\' COLLATE NOCASE OR
                    collection LIKE ? ESCAPE '\\' COLLATE NOCASE
                )
                ORDER BY kind, display COLLATE NOCASE
                """,
                (root_key, *(pattern for _ in range(6))),
            ).fetchall()

        results = []
        seen = set()
        for row in rows:
            key = (row["kind"], row["entity_path"])
            if key not in seen:
                seen.add(key)
                results.append(row["display"])
        report_progress(progress, f"Search complete · {len(results)} matches")
        return results
    finally:
        connection.close()


def invalidate_library(root: Path | None = None) -> None:
    path = database_path()
    if not path.exists():
        return
    connection = _connect(path)
    try:
        if root is None:
            connection.execute("DELETE FROM libraries")
        else:
            connection.execute(
                "DELETE FROM libraries WHERE root = ?",
                (str(Path(root).expanduser().resolve()),),
            )
        connection.commit()
    finally:
        connection.close()
