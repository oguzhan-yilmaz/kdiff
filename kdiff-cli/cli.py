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


    if not (left_is_dir and right_is_dir ):
        typer.echo("Error: Both paths must be directories")
        raise typer.Exit(1)
    elif (left_is_dir and right_is_dir):
        # TODO: compare the two folders
            # 1. get the list of files in the left folder
            # 2. get the list of files in the right folder
            # 3. create 3 lists: left_only, right_only, both
            # 4. print the lists
            # 5. if a file is in both lists, compare the contents
            # 5.1.  
        left_files = set(f.relative_to(left) for f in left.rglob('*') if f.is_file())
        right_files = set(f.relative_to(right) for f in right.rglob('*') if f.is_file())
        
        # Create the three lists
        left_only = list(left_files - right_files)
        right_only = list(right_files - left_files)
        both = list(left_files & right_files)
        
        # Print the lists
        typer.echo("\nFiles only in left folder:")
        for f in sorted(left_only):
            typer.echo(f"  {f}")
            
        typer.echo("\nFiles only in right folder:")
        for f in sorted(right_only):
            typer.echo(f"  {f}")
            
        typer.echo("\nFiles in both folders:")
        identical_count = 0
        for f in sorted(both):
            left_hash = hashlib.sha256((left / f).read_bytes()).hexdigest()
            right_hash = hashlib.sha256((right / f).read_bytes()).hexdigest()
            if left_hash != right_hash:
                typer.echo(f"  {f} (contents differ)")
            else:
                identical_count += 1
        
        if identical_count > 0:
            typer.echo(f"  {identical_count} identical files")

def main():
    app()

if __name__ == "__main__":
    main()

