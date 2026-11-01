import builtins
import json
import os
import typer

from pathlib import Path
from rich import print

from dontfeartheripper.scanner import scan_library
from dontfeartheripper.stats import build_stats
from dontfeartheripper.quality import analyze_quality
from dontfeartheripper.cover import (
    analyze_covers,
    preview_fetch,
    build_download_plan,
    execute_download_plan,
)
from dontfeartheripper.repair import (
    analyze_repairs,
    apply_repairs,
    undo_repairs,
)
from dontfeartheripper.container import (
    detect_containers,
    write_container_metadata,
    write_collection_nfo,
    write_container_poster,
)
from dontfeartheripper.organizer import (
    UNDO_FILE,
    apply_rename_plan,
    build_rename_plan,
    undo_renames,
)
from dontfeartheripper.jellyfin import (
    JellyfinError,
    generate_jellyfin_collections,
)

app = typer.Typer(help="dontfeartheripper v0.1.6")


@app.command()
def scan(
    path: str = typer.Argument("."),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output scan as JSON",
    ),
) -> None:
    items = scan_library(Path(path))

    if json_output:
        report = {
            "schema_version": 1,
            "items": [],
        }

        for item in items:
            report["items"].append(
                {
                    "path": str(item.path),
                    "category": item.category,
                    "artist": item.artist_name,
                    "album": item.album_name,
                    "tracks": item.track_count,
                    "flacs": item.flac_count,
                    "has_toc": item.has_toc,
                    "has_cue": item.has_cue,
                    "metadata_source": item.metadata_source,
                    "container": item.container_directory,
                    "cryptic": item.cryptic,
                    "rename_candidate": item.rename_candidate,
                    "suggested_name": item.suggested_name,
                    "disc_number": item.disc_number,
                    "rename_collision": item.rename_collision,
                }
            )

        builtins.print(json.dumps(report, indent=2))
        return

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
def doctor(
    path: str = typer.Argument("."),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output report as JSON",
    ),
) -> None:
    items = scan_library(Path(path))

    if json_output:
        report = {
            "schema_version": 1,
            "warnings": [],
            "info": [],
        }

        for item in items:
            if item.container_directory:
                report["info"].append(
                    {
                        "path": str(item.path),
                        "type": "container_directory",
                    }
                )

            if item.cryptic:
                report["warnings"].append(
                    {
                        "path": str(item.path),
                        "type": "cryptic_directory",
                        "suggested_name": item.suggested_name,
                        "collision": item.rename_collision,
                    }
                )

        builtins.print(json.dumps(report, indent=2))
        return

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

    plan = build_rename_plan(items)
    candidates = 0

    if not yes:
        print("[yellow]DRY RUN[/yellow]")

    for entry in plan:
        old_path = entry["from"]
        target = entry["to"]
        if entry["skip_reason"]:
            print()
            print(f"SKIP {old_path.name}")
            print(f" {entry['skip_reason']}")
            continue

        candidates += 1

        print()
        print(old_path.name)
        print(f" -> {target.name}")

    print()

    if candidates == 0:
        print("No rename candidates found.")
        return

    if yes:
        result = apply_rename_plan(plan)

        print(f"Renamed: {result['renamed']}")

        if result["renamed"]:
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

    result = undo_renames()

    for old_path, reason in result["skipped"]:
        print()
        print(f"SKIP {old_path}")
        print(f" {reason}")

    for operation in result["operations"]:
        print()
        print(f"UNDO {Path(operation['from']).name}")
        print(f"  -> {Path(operation['to']).name}")

    print()
    print(f"Reverted: {result['reverted']}")


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
        builtins.print(json.dumps(stats, indent=2))
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


@app.command()
def quality(
    path: str = typer.Argument("."),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output quality report as JSON",
    ),
) -> None:
    items = scan_library(Path(path))
    report = analyze_quality(items)

    if json_output:
        builtins.print(
            json.dumps(report, indent=2)
        )
        return

    issues = report["issues"]

    print()
    print(f"[cyan]Quality Score:[/cyan] {report['quality_score']}%")

    if not issues:
        print()
        print("[green]No quality issues found.[/green]")
        return

    for issue in issues:
        print()
        print(f"[yellow]WARN[/yellow] {issue['path']}")
        print(f"  {issue['type']}")

    print()
    print(f"Issues: {len(issues)}")
    print(f"Score: {report['quality_score']}%")


@app.command()
def repair(
    path: str = typer.Argument("."),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output repair plan as JSON",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Apply repairs",
    ),
) -> None:
    items = scan_library(Path(path))
    report = analyze_repairs(items)

    if json_output:
        builtins.print(
            json.dumps(report, indent=2)
        )
        return

    repairs = report["repairs"]

    if not repairs:
        print()
        print("[green]No repairs found.[/green]")
        return

    if not yes:
        print()
        print("[yellow]DRY RUN[/yellow]")

    rollback = []

    for repair in repairs:
        print()
        print(repair["path"])
        print(
            f"  {repair['field']}: "
            f'"{repair["old"]}" -> "{repair["new"]}"'
        )

        if yes:
            rollback.append(repair)

    print()
    print(f"Repairs: {len(repairs)}")

    if yes:
        applied = apply_repairs(repairs)

        print(f"Updated tags: {applied}")
        print("Rollback file: .dftr-last-repair.json")
    else:
        print("No changes were made.")
        print("Run with --yes to perform repairs.")


@app.command("repair-undo")
def repair_undo() -> None:
    reverted = undo_repairs()

    print()
    print(f"Reverted tags: {reverted}")


@app.command()
def cover(
    path: str = typer.Argument("."),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output cover report as JSON",
    ),
    fetch: bool = typer.Option(
        False,
        "--fetch",
        help="Preview MusicBrainz lookups",
    ),
    plan: bool = typer.Option(
        False,
        "--plan",
        help="Preview cover downloads",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Download cover art",
    ),
) -> None:

    items = scan_library(Path(path))

    if yes:
        preview_fetch(items)
        report = execute_download_plan(
            items
        )

        if json_output:

            builtins.print(
                json.dumps(
                    report,
                    indent=2,
                )
            )

            return

        ok = sum(
            1
            for item in report["downloads"]
            if item["success"] and not item["skipped"]
        )

        failed = sum(
            1
            for item in report["downloads"]
            if not item["success"]
        )

        skipped = sum(
            1
            for item in report["downloads"]
            if item["skipped"]
        )

        print()
        print(f"Downloaded: {ok}")
        print(f"Skipped: {skipped}")
        print(f"Failed: {failed}")

        return

    if plan:

        report = build_download_plan(items)

        if json_output:
            builtins.print(
                json.dumps(
                    report,
                    indent=2,
                )
            )
            return

        downloads = report["downloads"]

        print()
        print("[yellow]DOWNLOAD PLAN[/yellow]")

        for item in downloads:

            print()
            print(item["path"])

            print(
                f"  action: {item['action']}"
            )

            print(
                f"  target: {item['target_file']}"
            )

        print()
        print(
            f"Planned downloads: {len(downloads)}"
        )

        return


    if fetch:

        results = preview_fetch(items)

        if json_output:

            builtins.print(
                json.dumps(
                    {
                        "schema_version": 1,
                        "results": results,
                    },
                    indent=2,
                )
            )

            return

        found = 0

        print()
        print("[yellow]DRY RUN[/yellow]")

        for item in results:

            print()
            print(item["path"])

            if item["found"]:
                found += 1
                print("  MusicBrainz: match found")

                if item["cover_found"]:
                    print(
                        "  Cover Art Archive: cover found"
                    )
                else:
                    print(
                        "  Cover Art Archive: no cover"
                    )

            else:
                print("  MusicBrainz: no match")

        print()
        print(f"Candidates: {len(results)}")
        print(f"Found: {found}")
        print(f"Missing: {len(results) - found}")

        return

    report = analyze_covers(items)

    if json_output:
        builtins.print(
            json.dumps(report, indent=2)
        )
        return

    covers = report["missing_covers"]

    if not covers:
        print()
        print("[green]All albums have cover art.[/green]")
        return

    print()
    print("[yellow]Missing cover art[/yellow]")

    for item in covers:
        print()
        print(item["path"])

    print()
    print(f"Missing covers: {len(covers)}")

@app.command()
def container(
    path: str = typer.Argument("."),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Write container metadata files",
    ),
) -> None:

    containers = detect_containers(
        Path(path)
    )

    if not containers:

        print()
        print(
            "[green]No containers found.[/green]"
        )

        return

    written = 0

    print()
    print(
        f"Containers found: {len(containers)}"
    )

    for item in containers:

        print()
        print(item["path"])

        album_count = 0

        def _count(nodes):

            total = 0

            for node in nodes:

                if node["type"] == "album":
                    total += 1

                elif (
                    node["type"]
                    == "container"
                ):
                    total += _count(
                        node["children"]
                    )

            return total

        album_count = _count(
            item["children"]
        )

        print(
            f"  albums={album_count}"
        )

        target = (
            item["path"]
            / ".dftr-container.json"
        )

        print(
            f"  metadata={target.name}"
        )

        if yes:

            write_container_metadata(
                item
            )

            write_collection_nfo(
                item
            )

            write_container_poster(
                item
            )

            written += 1

    print()

    if yes:

        print(
            f"Metadata files written: {written}"
        )

    else:

        print(
            "Dry run only."
        )

        print(
            "Run with --yes to create metadata."
        )


@app.command()
def tui(
    path: str = typer.Argument(
        ".",
        help="Music library root",
    ),
) -> None:
    from dontfeartheripper.tui import run_tui

    run_tui(Path(path))


@app.command("jellyfin-collections")
def jellyfin_collections(
    path: str = typer.Argument(
        ".",
        help="Local music library root",
    ),
    url: str | None = typer.Option(
        None,
        "--url",
        help="Jellyfin server URL (or set JELLYFIN_URL)",
    ),
    server_root: str | None = typer.Option(
        None,
        "--server-root",
        help="Path to this library as seen by Jellyfin, if different",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Create/update collections on the Jellyfin server",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output the collection plan as JSON",
    ),
) -> None:
    library_root = Path(path).resolve()
    jellyfin_url = url or os.environ.get("JELLYFIN_URL")
    api_key = os.environ.get("JELLYFIN_API_KEY")

    if not jellyfin_url:
        raise typer.BadParameter(
            "provide --url or set JELLYFIN_URL"
        )
    if not api_key:
        raise typer.BadParameter(
            "set JELLYFIN_API_KEY in the environment"
        )
    if not library_root.is_dir():
        raise typer.BadParameter(
            f"library root is not a directory: {library_root}"
        )

    try:
        report = generate_jellyfin_collections(
            detect_containers(library_root),
            jellyfin_url,
            api_key,
            library_root,
            server_root=(
                server_root
                or os.environ.get("JELLYFIN_LIBRARY_ROOT")
            ),
            apply=yes,
        )
    except JellyfinError as exc:
        typer.echo(f"Jellyfin error: {exc}", err=True)
        raise typer.Exit(1) from exc

    if json_output:
        builtins.print(json.dumps(report, indent=2))
        return

    for collection in report["collections"]:
        state = (
            "UPDATE"
            if collection["collection_id"]
            else "CREATE"
        )
        print(
            f"[cyan]{state}[/cyan] {collection['name']}: "
            f"{collection['matched_count']}/{collection['album_count']} albums"
        )
        for missing in collection["missing_paths"]:
            print(f"  [yellow]NOT FOUND[/yellow] {missing}")

    if yes:
        for result in report["results"]:
            print(
                f"{result['status'].upper()} {result['name']}"
                + (
                    f": {result['reason']}"
                    if result.get("reason")
                    else ""
                )
            )
    else:
        print()
        print("Preview only; no Jellyfin collections were changed.")
        print("Run with --yes to create or synchronize collections.")


if __name__ == "__main__":
    app()
