import typer
import json
from pathlib import Path
from typing import Optional, Dict
from helpers import compare_folders, get_logger

app = typer.Typer()

@app.command()
def plan(
    left: Path = typer.Argument(..., help="Left folder path to compare", exists=True, dir_okay=True, file_okay=False),
    right: Path = typer.Argument(..., help="Right folder path to compare", exists=True, dir_okay=True, file_okay=False)
):
    """
    Compare two folders and show the differences between them
    Uses checksums.txt in each folder for content comparison
    """
    try:
        result = compare_folders(left, right)
        typer.echo(json.dumps(result, indent=2))
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)

@app.command()
def diff(
    left: Path = typer.Argument(..., help="Left folder path to compare", exists=True, dir_okay=True, file_okay=False),
    right: Path = typer.Argument(..., help="Right folder path to compare", exists=True, dir_okay=True, file_okay=False)
):
    """
    Compare two folders and wait for further input
    Uses checksums.txt in each folder for content comparison
    """
    try:
        result = compare_folders(left, right)
        typer.echo("result is got")
        
        
        
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


def main():
    app()

if __name__ == "__main__":
    main()

