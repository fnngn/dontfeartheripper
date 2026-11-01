import json
from pathlib import Path

from .atomic import atomic_write_text
from .progress import ProgressCallback, report_progress


UNDO_FILE = Path(".dftr-last-rename.json")


def build_rename_plan(items):
    plan = []

    for item in items:
        if not item.rename_candidate:
            continue

        target = item.path.parent / item.suggested_name
        skip_reason = None

        if item.rename_collision:
            skip_reason = "collision detected"
        elif target.exists():
            skip_reason = f"target already exists: {target.name}"

        plan.append(
            {
                "from": item.path,
                "to": target,
                "skip_reason": skip_reason,
            }
        )

    return plan


def apply_rename_plan(
    plan,
    progress: ProgressCallback | None = None,
):
    operations = []
    total = len(plan)

    for index, entry in enumerate(plan, start=1):
        report_progress(
            progress,
            f"Renaming {entry['from'].name}",
            index - 1,
            total,
        )
        if entry["skip_reason"]:
            continue

        old_path = entry["from"]
        new_path = entry["to"]

        if not old_path.exists():
            entry["skip_reason"] = "source directory is missing"
            continue

        if new_path.exists():
            entry["skip_reason"] = (
                f"target already exists: {new_path.name}"
            )
            continue

        old_path.rename(new_path)
        operations.append(
            {
                "from": str(old_path),
                "to": str(new_path),
            }
        )
        atomic_write_text(
            UNDO_FILE,
            json.dumps(operations, indent=2),
        )
        report_progress(
            progress,
            f"Renamed {old_path.name}",
            index,
            total,
        )

    return {
        "renamed": len(operations),
        "operations": operations,
    }


def undo_renames(progress: ProgressCallback | None = None):
    if not UNDO_FILE.exists():
        return {
            "reverted": 0,
            "skipped": [],
            "operations": [],
        }

    operations = json.loads(
        UNDO_FILE.read_text(encoding="utf-8")
    )
    reverted = 0
    skipped = []
    reverted_operations = []
    total = len(operations)

    for index, entry in enumerate(reversed(operations), start=1):
        old_path = Path(entry["from"])
        new_path = Path(entry["to"])
        report_progress(
            progress,
            f"Restoring {new_path.name}",
            index - 1,
            total,
        )

        if not new_path.exists():
            skipped.append((new_path, "target missing"))
            continue

        if old_path.exists():
            skipped.append(
                (old_path, "original path already exists")
            )
            continue

        new_path.rename(old_path)
        reverted += 1
        reverted_operations.append(
            {
                "from": str(new_path),
                "to": str(old_path),
            }
        )
        report_progress(
            progress,
            f"Restored {old_path.name}",
            index,
            total,
        )

    return {
        "reverted": reverted,
        "skipped": skipped,
        "operations": reverted_operations,
    }
