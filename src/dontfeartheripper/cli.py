import json
import typer

from pathlib import Path
from rich import print

from dontfeartheripper.scanner import scan_library
from dontfeartheripper.stats import build_stats

UNDO_FILE = Path(".dftr-last-rename.json")

app = typer.Typer(help="dontfeartheripper v0.0.4-dev")


@app.command()
def scan(path: str = typer.Argument(".")) -> None:
    items = scan_library(Path(path))

    for item in items:
        kind = item.category.upper()

        print(f"[cyan][{kind}][/cyan] {item.path.name}")

        if item.artist_name:
            print(f"  artist={item.artist_name}")

        if item.album_name:
            print(f"  album={item.album_name}")

        if item.track_count:
            print(f"  tracks={item.track_count}")

        print(f"  flacs={item.flac_count}")
        print(f"  toc={item.has_toc}")
        print(f"  cue={item.has_cue}")

        print(f"  source={item.metadata_source}")

        if item.container_directory:
            print("  container=yes")

        if item.cryptic:
            print("  cryptic=yes")

        print()


@app.command()
def doctor(path: str = typer.Argument(".")) -> None:
    items = scan_library(Path(path))

    for item in items:
        if item.container_directory:
            print(f"[blue]INFO[/blue] {item.path.name}")
            print("  container directory")
            print()

        if item.cryptic:
            print(f"[yellow]WARN[/yellow] {item.path.name}")
            print("  cryptic directory name")

            if item.rename_candidate:
                print(f"  suggested name: {item.suggested_name}")

            if item.rename_collision:
                print("  collision=yes")

            print()


@app.command()
def fix(
    path: str = typer.Argument("."),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Perform rename operations",
    ),
) -> None:
    items = scan_library(Path(path))

    renamed = 0
    candidates = 0
    rollback = []

    if not yes:
        print("[yellow]DRY RUN[/yellow]")

    for item in items:
        if not item.rename_candidate:
            continue

        if item.rename_collision:
            print()
            print(f"SKIP {item.path.name}")
            print(" collision detected")
            print(f" target: {item.suggested_name}")
            continue

        candidates += 1

        target = item.path.parent / item.suggested_name

        if target.exists():
            print()
            print(f"SKIP {item.path.name}")
            print(f" target already exists: {target.name}")
            continue

        print()
        print(item.path.name)
        print(f" -> {item.suggested_name}")

        if yes:
            rollback.append(
                {
                    "from": str(item.path),
                    "to": str(target),
                }
            )

            item.path.rename(target)
            renamed += 1

    print()

    if candidates == 0:
        print("No rename candidates found.")
        return

    if yes:
        UNDO_FILE.write_text(
            json.dumps(rollback, indent=2)
        )

        print(f"Renamed: {renamed}")

        if renamed:
            print(f"Rollback file: {UNDO_FILE}")
    else:
        print(f"Candidates: {candidates}")
        print("No changes were made.")
        print("Run with --yes to perform the rename.")


@app.command()
def undo() -> None:
    if not UNDO_FILE.exists():
        print("No rollback file found.")
        return

    operations = json.loads(
        UNDO_FILE.read_text()
    )

    reverted = 0

    for entry in reversed(operations):
        old_path = Path(entry["from"])
        new_path = Path(entry["to"])

        if not new_path.exists():
            print()
            print(f"SKIP {new_path}")
            print(" target missing")
            continue

        if old_path.exists():
            print()
            print(f"SKIP {old_path}")
            print(" original path already exists")
            continue

        print()
        print(f"UNDO {new_path.name}")
        print(f"  -> {old_path.name}")

        new_path.rename(old_path)
        reverted += 1

    print()
    print(f"Reverted: {reverted}")


@app.command()
def stats(
    path: str = typer.Argument("."),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output statistics as JSON",
    ),
) -> None:
    items = scan_library(Path(path))
    stats = build_stats(items)

    if json_output:
        print(json.dumps(stats, indent=2))
        return

    print()
    print("[cyan]Library Statistics[/cyan]")
    print()

    print(f"Albums:             {stats['albums']}")
    print(f"Compilations:       {stats['compilations']}")
    print(f"Soundtracks:        {stats['soundtracks']}")
    print()

    print(f"Containers:         {stats['containers']}")
    print(f"Cryptic:            {stats['cryptic']}")
    print()

    print(f"TOC files:          {stats['toc_files']}")
    print(f"CUE files:          {stats['cue_files']}")
    print()

    print(f"Rename candidates: {stats['rename_candidates']}")
    print(f"Collisions:         {stats['collisions']}")


if __name__ == "__main__":
    app()
