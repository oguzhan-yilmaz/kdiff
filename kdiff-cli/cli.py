import hashlib
import typer
from pathlib import Path
from typing import Optional

app = typer.Typer()

@app.command()
def diff(
    left: Path = typer.Argument(..., help="Left folder path to compare", exists=True, dir_okay=True, file_okay=False),
    right: Path = typer.Argument(..., help="Right folder path to compare", exists=True, dir_okay=True, file_okay=False)
):
    """
    Compare two folders and show the differences between them
    """
    # Check if paths are directories
    left_is_dir = left.is_dir()
    right_is_dir = right.is_dir()

    typer.echo(f"Comparing folders:\n{left}\n{right}")

    if not (left_is_dir and right_is_dir):
        typer.echo("Error: Both paths must be directories")
        raise typer.Exit(1)
    elif (left_is_dir and right_is_dir):
        # Compare the two folders
        # 1. Get the list of files in both folders
        left_files = set(f.relative_to(left) for f in left.rglob('*') if f.is_file())
        right_files = set(f.relative_to(right) for f in right.rglob('*') if f.is_file())
        
        # 2. Create three lists: left_only, right_only, both
        left_only = list(left_files - right_files)
        right_only = list(right_files - left_files)
        both = list(left_files & right_files)
        
        # 3. Print the results
        typer.echo("\nFiles only in left folder:")
        for f in sorted(left_only):
            typer.echo(f"  {f}")
            
        typer.echo("\nFiles only in right folder:")
        for f in sorted(right_only):
            typer.echo(f"  {f}")
            
        typer.echo("\nFiles in both folders:")
        identical_count = 0
        different_count = 0
        for f in sorted(both):
            left_hash = hashlib.sha256((left / f).read_bytes()).hexdigest()
            right_hash = hashlib.sha256((right / f).read_bytes()).hexdigest()
            if left_hash != right_hash:
                typer.echo(f"  {f} (contents differ)")
                different_count += 1
            else:
                identical_count += 1
        
        # 4. Print summary
        typer.echo(f"\nSummary:")
        typer.echo(f"  Files only in left: {len(left_only)}")
        typer.echo(f"  Files only in right: {len(right_only)}")
        typer.echo(f"  Identical files: {identical_count}")
        typer.echo(f"  Different files: {different_count}")

def main():
    app()

if __name__ == "__main__":
    main()

