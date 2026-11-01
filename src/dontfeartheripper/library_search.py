from pathlib import Path

from .library_db import search_index
from .progress import ProgressCallback


def search_library(
    root: Path,
    query: str,
    progress: ProgressCallback | None = None,
) -> list[str]:
    return search_index(root, query, progress)
