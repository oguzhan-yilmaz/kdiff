import typer
from pathlib import Path
from typing import Optional, Dict

app = typer.Typer()

def load_checksums(checksums_file: Path) -> Dict[str, str]:
    """
    Load checksums from a checksums.txt
    Expected format: hash filepath (one per line)
    Returns: dict mapping filepath to hash
    """
    checksums = {}
    if checksums_file.exists():
        with open(checksums_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    parts = line.split(None, 1)  # Split on whitespace, max 1 split
                    if len(parts) == 2:
                        hash_value, filepath = parts
                        checksums[filepath] = hash_value
    return checksums

@app.command()
def diff(
    left: Path = typer.Argument(..., help="Left folder path to compare", exists=True, dir_okay=True, file_okay=False),
    right: Path = typer.Argument(..., help="Right folder path to compare", exists=True, dir_okay=True, file_okay=False)
):
    """
    Compare two folders and show the differences between them
    Uses checksums.txt in each folder for content comparison
    """
    # Check if paths are directories
    left_is_dir = left.is_dir()
    right_is_dir = right.is_dir()

    typer.echo(f"Comparing folders:\n{left}\n{right}")

    if not (left_is_dir and right_is_dir):
        typer.echo("Error: Both paths must be directories")
        raise typer.Exit(1)
    elif (left_is_dir and right_is_dir):
        # Load checksums from both folders
        left_checksums_file = left / "checksums.txt"
        right_checksums_file = right / "checksums.txt"
        
        left_checksums = load_checksums(left_checksums_file)
        right_checksums = load_checksums(right_checksums_file)
        
        # Get the list of files from checksums (excluding checksums.txt itself)
        left_files = set(left_checksums.keys())
        right_files = set(right_checksums.keys())
        
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
            left_hash = left_checksums.get(f)
            right_hash = right_checksums.get(f)
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

