import typer
from pathlib import Path
from rich import print

from dontfeartheripper.scanner import scan_library
from dontfeartheripper.utils import sanitize_filename

app = typer.Typer(help="dontfeartheripper v0.0.2-dev")

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

            if item.artist_name and item.album_name:
                suggestion = sanitize_filename(f"{item.artist_name} - {item.album_name}")
                print(f"  suggested name: {suggestion}")
            elif item.album_name:
                suggestion = sanitize_filename(item.album_name)
                print(f"  suggested name: {suggestion}")

            print()


@app.command()
def fix(path: str = typer.Argument(".")) -> None:
    items = scan_library(Path(path))

    print("DRY RUN")

    for item in items:
        if not item.rename_candidate:
            continue

        print()
        print(item.path.name)
        print(f" -> {item.suggested_name}")

if __name__ == "__main__":
    app()
