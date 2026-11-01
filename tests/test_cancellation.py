import json
from pathlib import Path
import sys

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src"),
)

import pytest

from dontfeartheripper.models import LibraryItem
from dontfeartheripper.organizer import (
    apply_rename_plan,
    build_rename_plan,
    undo_renames,
)
from dontfeartheripper.repair import apply_repairs
from dontfeartheripper.progress import (
    CancellationToken,
    OperationCancelled,
)


def test_cancellation_token_raises_at_a_checkpoint():
    token = CancellationToken()
    token.cancel()

    with pytest.raises(OperationCancelled, match="cancelled safely"):
        token.raise_if_cancelled()


def test_cancelled_rename_keeps_completed_steps_recoverable(
    tmp_path,
    monkeypatch,
):
    source_paths = [tmp_path / "~first", tmp_path / "~second"]
    for path in source_paths:
        path.mkdir()
    monkeypatch.setattr(
        "dontfeartheripper.organizer.UNDO_FILE",
        tmp_path / "undo.json",
    )
    items = [
        LibraryItem(
            path=path,
            flac_count=1,
            has_toc=False,
            has_cue=False,
            category="album",
            cryptic=True,
            rename_candidate=True,
            suggested_name=f"Artist - {index}",
        )
        for index, path in enumerate(source_paths, start=1)
    ]

    def cancel_before_second_rename(message, current, total):
        if message == "Renaming ~second":
            raise OperationCancelled("Stopped by test.")

    with pytest.raises(OperationCancelled, match="Stopped by test"):
        apply_rename_plan(
            build_rename_plan(items),
            cancel_before_second_rename,
        )

    undo_file = tmp_path / "undo.json"
    assert json.loads(undo_file.read_text()) == [
        {
            "from": str(source_paths[0]),
            "to": str(tmp_path / "Artist - 1"),
        }
    ]
    assert (tmp_path / "Artist - 1").is_dir()
    assert source_paths[1].is_dir()

    result = undo_renames()

    assert result["reverted"] == 1
    assert all(path.is_dir() for path in source_paths)


def test_cancelled_tag_repair_keeps_a_rollback_journal(
    tmp_path,
    monkeypatch,
):
    paths = [tmp_path / "01.flac", tmp_path / "02.flac"]
    for path in paths:
        path.touch()
    values = {str(path): {"artist": ["Old Artist"]} for path in paths}
    monkeypatch.setattr(
        "dontfeartheripper.repair.REPAIR_UNDO_FILE",
        tmp_path / "repair-undo.json",
    )

    class FakeAudio:
        def __init__(self, path):
            self.path = str(path)

        def __contains__(self, field):
            return field in values[self.path]

        def __getitem__(self, field):
            return values[self.path][field]

        def __setitem__(self, field, value):
            values[self.path][field] = value

        def save(self):
            pass

    monkeypatch.setattr(
        "dontfeartheripper.repair.FLAC",
        FakeAudio,
    )

    def cancel_before_second_file(message, current, total):
        if message == "Updating tags: 02.flac":
            raise OperationCancelled("Stopped by test.")

    with pytest.raises(OperationCancelled):
        apply_repairs(
            [
                {
                    "field": "artist",
                    "files": [str(path) for path in paths],
                    "new": "New Artist",
                    "rule": "test",
                }
            ],
            cancel_before_second_file,
        )

    assert values[str(paths[0])]["artist"] == ["New Artist"]
    assert values[str(paths[1])]["artist"] == ["Old Artist"]
    assert json.loads(
        (tmp_path / "repair-undo.json").read_text()
    ) == [
        {
            "file": str(paths[0]),
            "field": "artist",
            "old": "Old Artist",
            "new": "New Artist",
            "rule": "test",
        }
    ]
