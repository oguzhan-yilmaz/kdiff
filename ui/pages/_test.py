import csv
import io
import html

def get_page_assets():
    """
    Returns the <link> (CSS) and <script> (JS) tags.
    Includes:
    1. Bootstrap 5 (Styling)
    2. DataTables (Sort/Filter/Pagination)
    3. jQuery (Required for DataTables)
    4. Custom logic for Rowspanning
    """
    css = """
    <link href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    
    <style>
        body { padding: 20px; background-color: #f8f9fa; }
        
        .table-container { 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            margin-top: 20px;
        }

        /* Long data handling */
        .data-cell {
            max-width: 250px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-family: monospace;
            font-size: 0.85rem;
            cursor: pointer;
        }

        .data-cell:hover {
            white-space: pre-wrap;
            word-break: break-word;
            position: absolute; /* Pops out */
            z-index: 100;
            background-color: #fff;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            min-width: 300px;
            border: 1px solid #ccc;
            padding: 5px;
        }

        /* Ensure vertical alignment for spanned rows */
        table.dataTable td {
            vertical-align: middle;
        }
    </style>
    """
    
    js = """
    <script src="https://code.jquery.com/jquery-3.7.0.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>

    <script>
        $(document).ready(function() {
            var table = $('#mainTable').DataTable({
                "pageLength": 25,
                "ordering": true,
                "searching": true,
                "lengthMenu": [10, 25, 50, 100],
                
                // This callback runs every time the table is drawn (sort, filter, page change)
                "drawCallback": function(settings) {
                    var api = this.api();
                    var rows = api.rows({page:'current'}).nodes();
                    var last = null;
                    
                    // COLUMNS TO GROUP: 
                    // Change [0, 1] to whatever column indexes you want to rowspan.
                    // Here we group by Column 0 (Name) and Column 1 (Namespace).
                    var groupColumns = [0, 1]; 

                    groupColumns.forEach(function(colIdx) {
                        var lastData = null;
                        var groupStart = null;
                        
                        api.column(colIdx, {page:'current'}).data().each(function(group, i) {
                            var row = rows[i];
                            var cell = $(row).find('td').eq(colIdx);
                            
                            if (lastData === group) {
                                // Data matches previous row: Hide this cell
                                cell.css('display', 'none');
                                // Increment rowspan of the group start
                                var rowspan = $(groupStart).attr('rowspan') || 1;
                                $(groupStart).attr('rowspan', parseInt(rowspan) + 1);
                            } else {
                                // New data: Reset logic
                                lastData = group;
                                groupStart = cell;
                                $(groupStart).attr('rowspan', 1);
                                $(groupStart).css('display', '');
                            }
                        });
                    });
                }
            });
        });
    </script>
    """
    return css, js

def generate_table_html(table_category, csv_data):
    """
    Parses CSV string and returns HTML structure.
    Adds ID 'mainTable' for DataTables targeting.
    """
    f = io.StringIO(csv_data.strip())
    reader = csv.reader(f)
    
    try:
        headers = next(reader)
    except StopIteration:
        return "<div class='alert alert-warning'>No data found.</div>"

    html_out = [f'<h3 class="mb-3 text-capitalize">{table_category} Data</h3>']
    
    # Note: Removed 'table-striped' because it looks confusing with rowspans
    html_out.append('<table id="mainTable" class="table table-bordered table-hover table-sm" style="width:100%">')
    
    # Header
    html_out.append('<thead class="table-dark"><tr>')
    for h in headers:
        html_out.append(f'<th>{html.escape(h)}</th>')
    html_out.append('</tr></thead>')
    
    # Body
    html_out.append('<tbody>')
    for row in reader:
        html_out.append('<tr>')
        for cell in row:
            safe_cell = html.escape(cell)
            # Add tooltip title for all cells
            cell_class = "data-cell" if len(safe_cell) > 50 else ""
            html_out.append(f'<td class="{cell_class}" title="{safe_cell}">{safe_cell}</td>')
        html_out.append('</tr>')
    html_out.append('</tbody>')
    html_out.append('</table>')
    
    return "\n".join(html_out)

if __name__ == "__main__":
    # --- DATA INPUT ---
    raw_csv_data = r'''name,namespace,uid,failed_jobs_history_limit,schedule,starting_deadline_seconds,successful_jobs_history_limit
kdiff-snapshots,kdiff,ea445e6b,2,00 20 * * *,90,5
kdiff-snapshots,kdiff,different-uid-1,2,00 21 * * *,90,5
grafana-snapshot,monitoring,b15ae22d,1,0 * * * *,,3
grafana-snapshot,monitoring,b15ae22d-2,1,0 * * * *,,3
grafana-snapshot,monitoring,b15ae22d-3,1,0 * * * *,,3
other-job,default,xyz-123,1,0 0 0 0 0,,1
'''
    
    # 1. Get Assets
    page_css, page_js = get_page_assets()
    
    # 2. Generate HTML (Parses CSV)
    table_html = generate_table_html("Kubernetes CronJobs", raw_csv_data)
    
    # 3. Assemble Full Report
    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Generated Report</title>
        {page_css}
    </head>
    <body>
        <div class="container-fluid">
            <h1>System Report</h1>
            <div class="table-container">
                {table_html}
            </div>
        </div>
        {page_js}
    </body>
    </html>
    """
    
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(full_html)
        
    print("Success: 'report.html' generated with DataTables, sorting, filtering, and rowspanning.")