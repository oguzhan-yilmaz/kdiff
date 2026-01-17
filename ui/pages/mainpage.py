import pandas as pd
import streamlit as st


def generate_complex_html(df, group_col, data_cols, note_col, table_class="custom-table"):
    """
    Generates HTML for a table where:
    1. group_col spans vertically across all its data rows + 1 note row.
    2. data_cols are rendered as normal rows.
    3. note_col is rendered as the final row for that group, spanning the data_cols.
    """
    
    # Start the table structure
    # We define headers based on the column names passed
    headers = [group_col] + data_cols
    header_html = "".join(f"<th>{h}</th>" for h in headers)
    
    html = f"""
    <table class="{table_class}">
        <thead>
            <tr>{header_html}</tr>
        </thead>
        <tbody>
    """
    
    # Group the dataframe by the main identifier (e.g., Project)
    # preserve_order ensures we output in the same order they appear
    groups = df[group_col].unique()
    
    for group_id in groups:
        # Get the subset of data for this group
        sub_df = df[df[group_col] == group_id]
        
        # Extract the Note (assuming it's the same for the whole group, take the first one)
        # If your note varies by row, you might want to join them or take the unique one.
        note_text = sub_df[note_col].iloc[0]
        
        # Calculate Rowspan: Number of data rows + 1 (for the note row)
        rowspan = len(sub_df) + 1
        
        # Iterate through the data rows
        for i, (_, row) in enumerate(sub_df.iterrows()):
            html += "<tr>"
            
            # 1. Render Group ID (Only on the very first row of the group)
            if i == 0:
                html += f'<td rowspan="{rowspan}" class="main-col">{group_id}</td>'
            
            # 2. Render Data Columns
            for col in data_cols:
                html += f"<td>{row[col]}</td>"
                
            html += "</tr>"
            
        # 3. Render the Note Row (Spans across all data columns)
        # colspan is equal to the number of data columns
        html += f"""
        <tr>
            <td colspan="{len(data_cols)}" class="note-row">{note_text}</td>
        </tr>
        """
        
    html += "</tbody></table>"
    
    return html
  
  
  
# 1. Define the CSS (You only need to do this once)
css = """
<style>
    .report-table {
        width: 100%;
        border-collapse: collapse;
        font-family: sans-serif;
        font-size: 14px;
        margin-bottom: 20px;
    }
    .report-table th {
        # background-color: #f0f2f6;
        text-align: left;
        padding: 12px;
        border-bottom: 2px solid #ddd;
    }
    .report-table td {
        border: 1px solid #e0e0e0;
        padding: 10px;
        vertical-align: top;
    }
    /* The merged ID column */
    .main-col {
        # background-color: #fafafa;
        font-weight: bold;
        vertical-align: middle;
        width: 150px;
        text-align: center;
    }
    /* The large text note at the bottom */
    .note-row {
        background-color: #fff9c4;
        color: #555;
        font-style: italic;
        padding: 10px;
        border-top: 2px dashed #e0e0e0 !important; /* Visual separation */
    }
</style>
"""

# 2. Create your DataFrame (Flat format)
data = [
    # Group 1
    {"Project": "Alpha", "Task": "Design UI",     "Status": "Done",    "Comments": "<b>Warning:</b> QA team is understaffed."},
    {"Project": "Alpha", "Task": "Backend API",   "Status": "Pending", "Comments": "<b>Warning:</b> QA team is understaffed."},
    # Group 2
    {"Project": "Beta",  "Task": "Database Mig",  "Status": "Done",    "Comments": "All looks good."},
    {"Project": "Beta",  "Task": "Testing",       "Status": "Done",    "Comments": "All looks good."},
    {"Project": "Beta",  "Task": "Deploy",        "Status": "Review",  "Comments": "All looks good."},
]
df = pd.DataFrame(data)

# 3. Generate HTML
html_output = generate_complex_html(
    df=df,
    group_col="Project",      # The column to merge vertically
    data_cols=["Task", "Status"], # The columns to list individually
    note_col="Comments",      # The column to put in the bottom row
    table_class="report-table"
)

# 4. Render
st.markdown(css, unsafe_allow_html=True)
st.markdown(html_output, unsafe_allow_html=True)



owinners_df = pd.read_json("https://www.ag-grid.com/example-assets/olympic-winners.json")
sample_df = owinners_df.sample(10)


sample_df
# 3. Generate HTML
html_output = generate_complex_html(
    df=df,
    group_col="country",      # The column to merge vertically
    # data_cols=["Task", "Status"], # The columns to list individually
    data_cols=[], # The columns to list individually
    note_col="Comments",      # The column to put in the bottom row
    table_class="report-table"
)

# 4. Render
st.markdown(css, unsafe_allow_html=True)
st.markdown(html_output, unsafe_allow_html=True)

