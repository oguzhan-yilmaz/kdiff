from datetime import datetime
import streamlit as st
from storage import get_kdiff_snapshot_metadata_files
import pandas as pd

st.markdown("# TAKE A DIFF🎈")
st.sidebar.markdown("# TAKE A DIFF🎈")

def main():
    s3_snapshot_dirs = get_kdiff_snapshot_metadata_files('test-bucket')

    snapshot_list = []

    for mf in s3_snapshot_dirs:
        data = mf['file_content']
        snapshot_info = data.get("snapshotInfo", {})
        timestamp = snapshot_info.get("timestamp")
        timestamp_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        snapshot_list.append({
            "Timestamp": timestamp_dt,
            "Output Directory": snapshot_info.get("output_directory"),
            "S3 Bucket": snapshot_info.get("s3_bucket_name"),
            "display": f"{timestamp_dt.strftime('%H:%M:%S')}"
        })

    df_snapshots = pd.DataFrame(snapshot_list)
    df_snapshots = df_snapshots.sort_values(by="Timestamp", ascending=True)

    col1, col2 = st.columns(2)

    snapshot_a = None
    snapshot_b = None

    with col1:
        st.header("Snapshot A")
        min_date_a = df_snapshots['Timestamp'].min().date()
        max_date_a = df_snapshots['Timestamp'].max().date()
        selected_date_a = st.date_input(
            "Filter snapshots by date",
            value=max_date_a,
            min_value=min_date_a,
            max_value=max_date_a,
            key="date_a"
        )
        
        df_filtered_a = df_snapshots[df_snapshots['Timestamp'].dt.date == selected_date_a]
        if not df_filtered_a.empty:
            snapshot_a = st.selectbox(
                "Select a snapshot",
                df_filtered_a['display'],
                key="snapshot_a"
            )
        else:
            st.warning("No snapshots found for this date.")

    with col2:
        st.header("Snapshot B")
        min_date_b = df_snapshots['Timestamp'].min().date()
        max_date_b = df_snapshots['Timestamp'].max().date()
        selected_date_b = st.date_input(
            "Filter snapshots by date",
            value=max_date_b,
            min_value=min_date_b,
            max_value=max_date_b,
            key="date_b"
        )

        df_filtered_b = df_snapshots[df_snapshots['Timestamp'].dt.date == selected_date_b]
        if not df_filtered_b.empty:
            snapshot_b = st.selectbox(
                "Select a snapshot",
                df_filtered_b['display'],
                key="snapshot_b"
            )
        else:
            st.warning("No snapshots found for this date.")

    if st.button("Compare"):
        if snapshot_a and snapshot_b:
            st.write("Comparing:")
            st.write(f"**Snapshot A:** {snapshot_a}")
            st.write(f"**Snapshot B:** {snapshot_b}")
            # Add comparison logic here
        else:
            st.error("Please select two snapshots to compare.")

if __name__ == '__main__':
    main()
