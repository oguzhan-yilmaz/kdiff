import typer
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Optional, Dict
from helpers import compare_folders, qsv_diff_different_files, get_logger, create_excel_from_backup

app = typer.Typer()


@app.command()
def excel(
    backup_path: Path = typer.Argument(
        ...,
        help="Path to the backup (tar file or folder)",
        exists=True,
    ),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output Excel file path (default: backup_name.xlsx)",
    ),
):
    """
    Create an Excel file from a backup (tar file or folder) containing all CSV files in different sheets
    """
    logger = get_logger()
    try:
        create_excel_from_backup(backup_path, output_path)
        logger.info("Excel file created successfully!")
    except Exception as e:
        logger.error(f"Error creating Excel file: {e}")
        raise typer.Exit(1)


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


@app.command()
def diff_excel(
    left_backup: Path = typer.Argument(
        ...,
        help="Left backup path (tar file or folder)",
        exists=True,
    ),
    right_backup: Path = typer.Argument(
        ...,
        help="Right backup path (tar file or folder)",
        exists=True,
    ),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output Excel file path (default: diff_<left>_vs_<right>.xlsx)",
    ),
):
    """
    Compare two backups (tar files or folders) and create a colored Excel file showing differences
    """
    logger = get_logger()
    try:
        from helpers import create_diff_excel
        create_diff_excel(left_backup, right_backup, output_path)
        logger.info("Diff Excel file created successfully!")
    except Exception as e:
        logger.error(f"Error creating diff Excel file: {e}")
        raise typer.Exit(1)


def main():
    app()


if __name__ == "__main__":
    main()
