import typer
import json
import subprocess
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
    try:
        result = compare_folders(left, right)
        typer.echo("Comparison completed. Processing different files...")
        
        # Create diff directory if it doesn't exist
        diff_dir = Path("diff")
        diff_dir.mkdir(exist_ok=True)
        
        # Process different files
        different_files = result.get("different_files", [])
        
        if not different_files:
            typer.echo("No different files found.")
            return
        
        typer.echo(f"Found {len(different_files)} different files to process:")
        
        for file_path in different_files:
            # Check if it's a CSV file
            if not file_path.endswith('.csv'):
                typer.echo(f"Skipping non-CSV file: {file_path}")
                continue
            
            # Construct full paths
            left_file = left / file_path
            right_file = right / file_path
            
            # Check if both files exist
            if not left_file.exists():
                typer.echo(f"Warning: Left file does not exist: {left_file}")
                continue
            if not right_file.exists():
                typer.echo(f"Warning: Right file does not exist: {right_file}")
                continue
            
            # Create output diff file path
            diff_file = diff_dir / f"{Path(file_path).stem}.diff.csv"
            
            # Run qsv diff command
            cmd = [
                "qsv", "diff", 
                "--drop-equal-fields",
                str(left_file),
                str(right_file)
            ]
            
            typer.echo(f"Processing: {file_path}")
            typer.echo(f"Command: {' '.join(cmd)} > {diff_file}")
            
            try:
                with open(diff_file, 'w') as output_file:
                    subprocess.run(cmd, stdout=output_file, check=True)
                typer.echo(f"✓ Diff saved to: {diff_file}")
            except subprocess.CalledProcessError as e:
                typer.echo(f"✗ Error running qsv diff for {file_path}: {e}")
            except Exception as e:
                typer.echo(f"✗ Unexpected error processing {file_path}: {e}")
        
        typer.echo(f"\nDiff processing completed. Results saved in: {diff_dir}")
        
        # Wait for user input to continue
        typer.echo("\nPress Enter to continue...")
        input()
        
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


def main():
    app()

if __name__ == "__main__":
    main()

