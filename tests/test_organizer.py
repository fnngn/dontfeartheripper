from dontfeartheripper.models import LibraryItem
from dontfeartheripper.organizer import (
    apply_rename_plan,
    build_rename_plan,
    undo_renames,
)


def test_rename_plan_can_be_applied_and_undone(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "~cryptic"
    source.mkdir()
    monkeypatch.setattr(
        "dontfeartheripper.organizer.UNDO_FILE",
        tmp_path / "undo.json",
    )
    item = LibraryItem(
        path=source,
        flac_count=1,
        has_toc=False,
        has_cue=False,
        category="album",
        cryptic=True,
        rename_candidate=True,
        suggested_name="Artist - Album",
    )

    plan = build_rename_plan([item])
    applied = apply_rename_plan(plan)

    assert applied["renamed"] == 1
    assert (tmp_path / "Artist - Album").is_dir()

    undone = undo_renames()

    assert undone["reverted"] == 1
    assert source.is_dir()
    assert not (tmp_path / "Artist - Album").exists()


def test_rename_plan_skips_existing_target(tmp_path):
    source = tmp_path / "~cryptic"
    target = tmp_path / "Artist - Album"
    source.mkdir()
    target.mkdir()
    item = LibraryItem(
        path=source,
        flac_count=1,
        has_toc=False,
        has_cue=False,
        category="album",
        cryptic=True,
        rename_candidate=True,
        suggested_name=target.name,
    )

    plan = build_rename_plan([item])

    assert len(plan) == 1
    assert plan[0]["skip_reason"] == (
        "target already exists: Artist - Album"
    )
    assert source.is_dir()
