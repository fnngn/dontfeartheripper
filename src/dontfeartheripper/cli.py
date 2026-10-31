import typer

app = typer.Typer(help="dontfeartheripper v0.0.1")


@app.command()
def scan(
    path: str = typer.Argument(".", help="Path to scan")
) -> None:
    print(f"Scanning: {path}")


@app.command()
def fix(
    path: str = typer.Argument(".", help="Path to fix")
) -> None:
    print(f"Fixing: {path}")


if __name__ == "__main__":
    app()
