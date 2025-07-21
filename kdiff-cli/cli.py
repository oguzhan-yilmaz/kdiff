import typer
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict
from helpers import compare_folders, qsv_diff_different_files, get_logger

app = typer.Typer()


@app.command()
def plan(
    left: Path = typer.Argument(
        ...,
        help="Left folder path to compare",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    right: Path = typer.Argument(
        ...,
        help="Right folder path to compare",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
):
    """
    Compare two folders and show the differences between them
    Uses checksums.txt in each folder for content comparison
    """
    logger = get_logger()
    try:
        result = compare_folders(left, right)
        typer.echo(json.dumps(result, indent=2))
    except ValueError as e:
        logger.error(f"Error: {e}")
        raise typer.Exit(1)


@app.command()
def diff(
    left: Path = typer.Argument(
        ...,
        help="Left folder path to compare",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    right: Path = typer.Argument(
        ...,
        help="Right folder path to compare",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
):
    logger = get_logger()
    try:
        result = compare_folders(left, right)
        logger.info("Comparison completed. Processing different files...")

        # Process different files
        different_files = result.get("different_files", [])
        qsv_diff_different_files(left, right, different_files)

    except ValueError as e:
        logger.error(f"Error: {e}")
        raise typer.Exit(1)


def main():
    app()


if __name__ == "__main__":
    main()
