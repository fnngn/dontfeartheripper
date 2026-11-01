import os
from pathlib import Path
import shutil
import tempfile


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path = Path(path)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(data)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def atomic_write_text(
    path: Path,
    text: str,
    encoding: str = "utf-8",
) -> None:
    atomic_write_bytes(Path(path), text.encode(encoding))


def atomic_copy_file(source: Path, destination: Path) -> None:
    source = Path(source)
    destination = Path(destination)
    temporary_path = None
    try:
        with source.open("rb") as source_file:
            with tempfile.NamedTemporaryFile(
                dir=destination.parent,
                prefix=f".{destination.name}.",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                shutil.copyfileobj(source_file, temporary_file)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
