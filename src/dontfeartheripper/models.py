from dataclasses import dataclass
from pathlib import Path

@dataclass
class LibraryItem:
    path: Path
    flac_count: int
    has_toc: bool
    has_cue: bool
    category: str
    cryptic: bool
    album_name: str | None = None
    artist_name: str | None = None
    track_count: int = 0
    metadata_source: str = "unknown"
    container_directory: bool = False
    rename_candidate: bool = False
    suggested_name: str | None = None
    disc_number: int | None = None
    rename_collision: bool = False
    genre: str | None = None
