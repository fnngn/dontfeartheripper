import typer
from pathlib import Path
from rich import print

from dontfeartheripper.scanner import scan_library

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
            print()

@app.command()
def fix(path: str = typer.Argument(".")):
    print(f"Fixing: {path}")

if __name__ == "__main__":
    app()
