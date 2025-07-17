import typer
import json
import subprocess
import logging
import os
from pathlib import Path
from typing import Optional, Dict


def get_logger(name: str = "kdiff") -> logging.Logger:
    """
    Get a logger instance with level set from KDIFF_LOGLEVEL environment variable.
    
    Args:
        name: The name of the logger
        
    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure the logger if it hasn't been configured yet
    if not logger.handlers:
        # Get log level from environment variable
        log_level_str = os.getenv("KDIFF_LOGLEVEL", "INFO").upper()
        
        # Map string levels to logging constants
        level_mapping = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        
        log_level = level_mapping.get(log_level_str, logging.INFO)
        
        # Configure the logger
        logger.setLevel(log_level)
        
        # Create console handler if none exists
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    return logger 


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

def compare_folders(left: Path, right: Path) -> Dict:
    """
    Compare two folders and return the differences as a JSON-serializable dictionary
    """
    # Check if paths are directories
    left_is_dir = left.is_dir()
    right_is_dir = right.is_dir()

    if not (left_is_dir and right_is_dir):
        raise ValueError("Both paths must be directories")
    
    # Load checksums from both folders
    left_checksums_file = left / "checksums.txt"
    right_checksums_file = right / "checksums.txt"
    
    left_checksums = load_checksums(left_checksums_file)
    right_checksums = load_checksums(right_checksums_file)
    
    # Get the list of files from checksums (excluding checksums.txt itself)
    left_files = set(left_checksums.keys())
    right_files = set(right_checksums.keys())
    
    # Create three lists: left_only, right_only, both
    left_only = list(left_files - right_files)
    right_only = list(right_files - left_files)
    both = list(left_files & right_files)
    
    # Analyze files in both folders
    identical_files = []
    different_files = []
    
    for f in sorted(both):
        left_hash = left_checksums.get(f)
        right_hash = right_checksums.get(f)
        if left_hash != right_hash:
            different_files.append(f)
        else:
            identical_files.append(f)
    
    # Return structured data
    return {
        "left_path": str(left),
        "right_path": str(right),
        "files_only_in_left": sorted(left_only),
        "files_only_in_right": sorted(right_only),
        "identical_files": identical_files,
        "different_files": different_files,
        "summary": {
            "files_only_in_left": len(left_only),
            "files_only_in_right": len(right_only),
            "identical_files": len(identical_files),
            "different_files": len(different_files)
        }
    }




def qsv_diff_different_files(left: Path, right: Path, different_files: list) -> None:
    """
    Process different files and run qsv diff on CSV files
    """
    logger = get_logger()
    
    # Create diff directory if it doesn't exist
    diff_dir = Path("diff")
    diff_dir.mkdir(exist_ok=True)
    
    if not different_files:
        logger.info("No different files found.")
        return
    
    logger.info(f"Found {len(different_files)} different files to process:")
    
    for file_path in different_files:
        # Check if it's a CSV file
        if not file_path.endswith('.csv'):
            logger.info(f"Skipping non-CSV file: {file_path}")
            continue
        
        # Construct full paths
        left_file = left / file_path
        right_file = right / file_path
        
        # Check if both files exist
        if not left_file.exists():
            logger.warning(f"Left file does not exist: {left_file}")
            continue
        if not right_file.exists():
            logger.warning(f"Right file does not exist: {right_file}")
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
        
        logger.info(f"Processing: {file_path}")
        logger.debug(f"Command: {' '.join(cmd)} > {diff_file}")
        
        try:
            with open(diff_file, 'w') as output_file:
                subprocess.run(cmd, stdout=output_file, check=True)
            logger.info(f"✓ Diff saved to: {diff_file}")
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Error running qsv diff for {file_path}: {e}")
        except Exception as e:
            logger.error(f"✗ Unexpected error processing {file_path}: {e}")
    
    logger.info(f"Diff processing completed. Results saved in: {diff_dir}")