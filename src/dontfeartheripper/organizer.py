import json
from pathlib import Path


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


def apply_rename_plan(plan):
    operations = []

    for entry in plan:
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
        UNDO_FILE.write_text(
            json.dumps(operations, indent=2),
            encoding="utf-8",
        )

    return {
        "renamed": len(operations),
        "operations": operations,
    }


def undo_renames():
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

    for entry in reversed(operations):
        old_path = Path(entry["from"])
        new_path = Path(entry["to"])

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

    return {
        "reverted": reverted,
        "skipped": skipped,
        "operations": reverted_operations,
    }
