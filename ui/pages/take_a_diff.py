from datetime import datetime
import streamlit as st
from storage import get_kdiff_snapshot_metadata_files
import pandas as pd
from config import bucket_name
from misc import compare_checksums

st.markdown("# TAKE A DIFF🎈")
st.sidebar.markdown("# TAKE A DIFF🎈")


def main():
    s3_snapshot_dirs = get_kdiff_snapshot_metadata_files('test-bucket')

    snapshot_list = []

    for mf in s3_snapshot_dirs:
        data = mf['metadata_json']
        snapshot_info = data.get("snapshotInfo", {})
        timestamp = snapshot_info.get("timestamp")
        timestamp_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        snapshot_list.append({
            "Timestamp": timestamp_dt,
            "Output Directory": snapshot_info.get("output_directory"),
            "S3 Bucket": snapshot_info.get("s3_bucket_name"),
            "display": f"{timestamp_dt.strftime('%H:%M:%S')}",
            "checksums": data.get("checksums", {})
        })

    df_snapshots = pd.DataFrame(snapshot_list)
    df_snapshots = df_snapshots.sort_values(by="Timestamp", ascending=True)

    col1, col2 = st.columns(2)

    snapshot_a_display = None
    snapshot_b_display = None

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
            snapshot_a_display = st.selectbox(
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
            snapshot_b_display = st.selectbox(
                "Select a snapshot",
                df_filtered_b['display'],
                key="snapshot_b"
            )
        else:
            st.warning("No snapshots found for this date.")

    if st.button("Compare"):
        if snapshot_a_display and snapshot_b_display:
            
            snapshot_a_data = df_snapshots[df_snapshots['display'] == snapshot_a_display].iloc[0]
            snapshot_b_data = df_snapshots[df_snapshots['display'] == snapshot_b_display].iloc[0]

            checksums_a = snapshot_a_data['checksums']
            checksums_b = snapshot_b_data['checksums']

            new_objects, deleted_objects, changed_objects = compare_checksums(checksums_a, checksums_b)

            st.header("New Objects")
            st.dataframe(pd.DataFrame(list(new_objects.items()), columns=['Object', 'Checksum']))

            st.header("Changed Objects")
            changed_df = pd.DataFrame([(k, v[0], v[1]) for k, v in changed_objects.items()], columns=['Object', 'Checksum A', 'Checksum B'])
            st.dataframe(changed_df)

            st.header("Deleted Objects")
            st.dataframe(pd.DataFrame(list(deleted_objects.items()), columns=['Object', 'Checksum']))

        else:
            st.error("Please select two snapshots to compare.")

if __name__ == '__main__':
    main()
