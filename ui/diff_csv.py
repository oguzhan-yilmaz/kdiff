from pathlib import Path
import subprocess
import streamlit as st
from s3_and_local_files import run_any_bash_command
# import os
# import tempfile
# from typing import Optional, Dict
# import pandas as pd


def qsv_diff_different_files(left_file: Path, right_file: Path, save_file: Path) -> None:
    # Construct full paths
    # Check if both files exist
    if not left_file.exists():
        st.warning(f"Left file does not exist: {left_file}")
        return False
    if not right_file.exists():
        st.warning(f"Right file does not exist: {right_file}")
        return False

    # Run qsv diff command
    cmd = ' '.join([
        "qsv",
        "diff",
        "--drop-equal-fields",
        "--key",
        "namespace,name",
        # "--sort-columns namespace,name",
        str(left_file),
        str(right_file),
    ])

    # try:
    #     with open(diff_file, "w") as output_file:
    #         subprocess.run(cmd, stdout=output_file, check=True)
    #     logger.info(f"✓ Diff saved to: {diff_file}")
    # except subprocess.CalledProcessError as e:
    #     logger.error(f"✗ Error running qsv diff for {file_path}: {e}")
    # except Exception as e:
    #     logger.error(f"✗ Unexpected error processing {file_path}: {e}")

    out = run_any_bash_command(cmd)
    st.markdown("# -----------")
    out
    return out
