from pathlib import Path
import subprocess
import streamlit as st
from s3_and_local_files import run_any_bash_command
# import os
# import tempfile
# from typing import Optional, Dict
# import pandas as pd
import json

def qsv_diff_different_files(left_file: Path, right_file: Path, id_column: str, sp_connection_name: str) -> str:
    # Construct full paths
    # Check if both files exist
    if not left_file.exists():
        st.warning(f"Left file does not exist: {left_file}")
        return False
    if not right_file.exists():
        st.warning(f"Right file does not exist: {right_file}")
        return False
    cmd = f"""
    QSV_SKIP_FORMAT_CHECK=true qsv diff --drop-equal-fields --key {id_column} \
        <(qsv search -s sp_connection_name '{sp_connection_name}' {str(left_file)}) \
        <(qsv search -s sp_connection_name '{sp_connection_name}' {str(right_file)})
    """

    # print(cmd)
    out = run_any_bash_command(cmd)
    # print(out)
    # print('------------------')
    return out
