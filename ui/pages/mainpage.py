import streamlit as st
import pandas as pd
import numpy as np

st.title("📊 Custom Rowspan Control")

st.info("Create tables with rowspan on specific cells only")

# Example 1: Selective rowspan on specific cells
st.header("1. Selective Rowspan - Choose Which Cells Span")

data1 = {
    'Product': ['Laptop', '', '', 'Phone', '', 'Tablet'],
    'Category': ['Electronics', '', '', 'Electronics', '', 'Electronics'],
    'Model': ['Pro 15', 'Pro 13', 'Air', 'X Pro', 'X Standard', 'Mini'],
    'Price': [1500, 1200, 900, 1000, 800, 600],
    'Stock': [50, 30, 40, 100, 150, 80]
}

df1 = pd.DataFrame(data1)

def create_custom_rowspan_table(df, rowspan_config):
    """
    Create table with custom rowspan control
    
    rowspan_config: dict like {'column_name': [(start_row, span_count), ...]}
    Example: {'Product': [(0, 3), (3, 2)], 'Category': [(0, 6)]}
    """
    
    html = """
    <style>
        .custom-table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        .custom-table th {
            padding: 12px;
            text-align: left;
            border: 1px solid #ddd;
            font-weight: 600;
        }
        .custom-table td {
            padding: 10px 12px;
            border: 1px solid #ddd;
        }
        .custom-table tr:hover {
        }
        .span-cell {
            font-weight: 500;
            vertical-align: middle;
        }
    </style>
    <table class="custom-table">
        <thead>
            <tr>
    """
    
    # Add headers
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    
    # Track which cells to skip (already covered by rowspan)
    skip_cells = {col: set() for col in df.columns}
    
    # Add data rows
    for row_idx in range(len(df)):
        html += "<tr>"
        
        for col in df.columns:
            # Skip if this cell is covered by a rowspan from above
            if row_idx in skip_cells[col]:
                continue
            
            # Check if this cell should have rowspan
            cell_value = df.iloc[row_idx][col]
            rowspan = 1
            is_span_cell = False
            
            if col in rowspan_config:
                for start_row, span_count in rowspan_config[col]:
                    if row_idx == start_row:
                        rowspan = span_count
                        is_span_cell = True
                        # Mark subsequent rows as skip
                        for skip_idx in range(start_row + 1, start_row + span_count):
                            skip_cells[col].add(skip_idx)
                        break
            
            # Format value
            if isinstance(cell_value, (int, float)) and cell_value > 100:
                formatted = f"${cell_value:,.0f}" if 'Price' in col or 'Revenue' in col else f"{cell_value:,.0f}"
            else:
                formatted = cell_value if cell_value != '' else ''
            
            # Add cell with or without rowspan
            cell_class = ' class="span-cell"' if is_span_cell else ''
            if rowspan > 1:
                html += f'<td{cell_class} rowspan="{rowspan}">{formatted}</td>'
            else:
                html += f'<td>{formatted}</td>'
        
        html += "</tr>"
    
    html += "</tbody></table>"
    return html

# Product spans 3 rows (0-2), then 2 rows (3-4), then 1 row (5)
# Category spans all 6 rows
rowspan_config1 = {
    'Product': [(0, 3), (3, 2), (5, 1)],
    'Category': [(0, 6)]
}

html1 = create_custom_rowspan_table(df1, rowspan_config1)
st.markdown(html1, unsafe_allow_html=True)

st.code("""
rowspan_config = {
    'Product': [(0, 3), (3, 2), (5, 1)],  # Row 0 spans 3, row 3 spans 2, row 5 spans 1
    'Category': [(0, 6)]  # Row 0 spans all 6 rows
}
""")

st.markdown("---")

# Example 2: Side-by-side rowspans
st.header("2. Multiple Columns with Independent Rowspans")

data2 = {
    'Region': ['North', '', '', 'South', '', 'West'],
    'Manager': ['Alice', 'Alice', '', 'Bob', '', 'Carol'],
    'City': ['NYC', 'Boston', 'Philadelphia', 'Miami', 'Atlanta', 'LA'],
    'Sales': [500, 400, 300, 600, 450, 700],
    'Status': ['Active', '', '', 'Active', '', 'Active']
}

df2 = pd.DataFrame(data2)

# Region: North spans 3, South spans 2, West spans 1
# Manager: Alice spans 2, Bob spans 1, Carol spans 1
# Status: spans match Region
rowspan_config2 = {
    'Region': [(0, 3), (3, 2), (5, 1)],
    'Manager': [(0, 2), (2, 1), (3, 1), (4, 1), (5, 1)],
    'Status': [(0, 3), (3, 2), (5, 1)]
}

html2 = create_custom_rowspan_table(df2, rowspan_config2)
st.markdown(html2, unsafe_allow_html=True)

st.markdown("---")

# Example 3: Interactive configuration
st.header("3. Interactive Rowspan Builder")

st.markdown("Configure your own table with custom rowspans:")

# Sample data
data3 = {
    'Team': ['Engineering', '', '', '', 'Sales', '', 'HR'],
    'Department': ['Frontend', '', 'Backend', '', 'East', 'West', 'Recruiting'],
    'Employee': ['John', 'Jane', 'Mike', 'Sarah', 'Tom', 'Lisa', 'Emma'],
    'Salary': [120000, 115000, 130000, 125000, 80000, 85000, 75000]
}

df3 = pd.DataFrame(data3)

st.subheader("Configure Rowspans")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Team column:**")
    team_span1 = st.number_input("First span (from row 0)", 1, 7, 4, key='team1')
    team_span2_start = team_span1
    team_span2 = st.number_input(f"Second span (from row {team_span2_start})", 1, 7-team_span1, 2, key='team2')
    team_span3_start = team_span1 + team_span2
    team_span3 = 7 - team_span1 - team_span2

with col2:
    st.markdown("**Department column:**")
    dept_span1 = st.number_input("First span (from row 0)", 1, 7, 2, key='dept1')
    dept_span2_start = dept_span1
    dept_span2 = st.number_input(f"Second span (from row {dept_span2_start})", 1, 7-dept_span1, 2, key='dept2')

# Build config
rowspan_config3 = {
    'Team': [(0, team_span1), (team_span2_start, team_span2)]
}

if team_span3 > 0:
    rowspan_config3['Team'].append((team_span3_start, team_span3))

rowspan_config3['Department'] = [(0, dept_span1), (dept_span2_start, dept_span2)]

remaining = 7 - dept_span1 - dept_span2
if remaining > 0:
    rowspan_config3['Department'].append((dept_span1 + dept_span2, remaining))

html3 = create_custom_rowspan_table(df3, rowspan_config3)
st.markdown(html3, unsafe_allow_html=True)

st.code(f"rowspan_config = {rowspan_config3}")

st.markdown("---")

# Example 4: Complex mixed rowspans
st.header("4. Complex Layout Example")

data4 = {
    'Project': ['Website', '', '', '', 'Mobile App', '', 'Backend'],
    'Phase': ['Design', '', 'Development'*10, '', 'Design', 'Development', 'API'],
    'Task': ['Wireframes', 'Mockups', 'Frontend', 'Backend '*10, 'UI/UX', 'Implementation '*10, 'REST API'],
    'Hours': [40, 60, 120, 100, 80, 200, 150],
    'Status': ['Done', 'Done', 'In Progress', '', 'Done', 'In Progress', 'Planning']
}

df4 = pd.DataFrame(data4)

rowspan_config4 = {
    'Project': [(0, 4), (4, 2), (6, 1)],
    'Phase': [(0, 2), (2, 2), (4, 1), (5, 1), (6, 1)],
    'Status': [(2, 2), (5, 1)]
}

html4 = create_custom_rowspan_table(df4, rowspan_config4)
st.markdown(html4, unsafe_allow_html=True)

st.markdown("### How to use:")
st.markdown("""
1. Define your DataFrame with empty strings ('') where cells should be merged
2. Create a `rowspan_config` dictionary:
   - Keys are column names
   - Values are lists of tuples: `(start_row_index, number_of_rows_to_span)`
3. Example: `{'Product': [(0, 3), (3, 2)]}` means:
   - Row 0 in 'Product' column spans 3 rows
   - Row 3 in 'Product' column spans 2 rows
""")