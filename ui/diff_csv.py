from pathlib import Path
import subprocess
import streamlit as st
from s3_and_local_files import run_any_bash_command
# import os
# import tempfile
# from typing import Optional, Dict
# import pandas as pd
import json
from schema_types import get_data_tables_from_multiple_schemas



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
        "uid",
        # "--sort-columns namespace,name",
        str(left_file),
        str(right_file),
        "|", "tee", str(save_file)
    ])

    out = run_any_bash_command(cmd)
    return out
