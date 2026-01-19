import streamlit as st

# 1. Define Data (Variable number of rows per project)
data = [
    {
        "id": "Project Alpha",
        "tasks": [
            {"name": "Design", "status": "Done"},
            {"name": "Dev", "status": "In Progress"},
            {"name": "Testing", "status": "Pending"}, # 3 tasks
        ],
        "note": "<b>Warning:</b> Staff shortage in QA dept.<b>Warning:</b><br/> Staff shortage in QA dept.<b>Warning:</b><br/> Staff shortage in QA dept.<b>Warning:</b> <br/> Staff shortage in QA dept.<b>Warning:</b><br/> Staff shortage in QA dept.<b>Warning:</b> Staff shortage in QA dept."
    },
    {
        "id": "Project Beta",
        "tasks": [
            {"name": "Kickoff", "status": "Done"}, # 1 task
        ],
        "note": "<b>Update:</b> Budget approved.<b>Update:</b> Budget approved.<b>Update:</b> Budget approved.<b>Update:</b> Budget approved.<b>Update:</b> Budget approved.<b>Update:</b> Budget approved."
    }
]

# 2. Build HTML
# We verify the rowspan calculation: (Number of Tasks) + 1 (for the Note row)
html = """
<style>
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-family: sans-serif;
        font-size: 14px;
    }
    .custom-table th {
        text-align: left;
        padding: 10px;
        border-bottom: 2px solid #ddd;
    }
    .custom-table td {
        border: 1px solid #e0e0e0;
        padding: 8px;
        vertical-align: top;
    }
    .main-col {
        font-weight: bold;
        vertical-align: middle;
        width: 150px;
    }
    .note-row {
        background-color: #fffde7;
        color: #666;
        font-style: italic;
        font-size: 0.9em;
    }
</style>

<table class="custom-table">
    <thead>
        <tr>
            <th>Project</th>
            <th>Task</th>
            <th>Status</th>
        </tr>
    </thead>
    <tbody>
"""

for project in data:
    tasks = project['tasks']
    # Rowspan = All task rows + 1 row for the note
    total_span = len(tasks) + 1
    
    # --- Loop through tasks ---
    for i, task in enumerate(tasks):
        html += "<tr>"
        
        # IF this is the FIRST task, render the Main Project Cell
        if i == 0:
            html += f'<td rowspan="{total_span}" class="main-col">{project["id"]}</td>'
            
        # Render the task columns
        html += f'<td>{task["name"]}</td>'
        html += f'<td>{task["status"]}</td>'
        html += "</tr>"

    # --- After all tasks, add the Note Row (spans 2 columns: Task + Status) ---
    html += f"""
    <tr>
        <td colspan="2" class="note-row">{project['note']}</td>
    </tr>
    """

html += "</tbody></table>"
print(html)
# 3. RENDER - This exact line is critical
st.markdown(html, unsafe_allow_html=True)