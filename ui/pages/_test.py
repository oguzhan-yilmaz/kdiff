import csv
import io
import html

def get_page_assets():
    """
    Returns the <link> (CSS) and <script> (JS) tags.
    Includes Bootstrap 5 via CDN and custom styles for data handling.
    """
    css = """
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding: 20px; background-color: #f8f9fa; }
        .table-container { 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            overflow-x: auto;
        }
        /* Handle long JSON data in cells */
        .data-cell {
            max-width: 300px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-family: monospace;
            font-size: 0.85rem;
            cursor: pointer;
        }
        /* Expand on hover (optional UI enhancement) */
        .data-cell:hover {
            white-space: pre-wrap;
            word-break: break-word;
            position: relative;
            z-index: 100;
            background-color: #fff;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            min-width: 300px;
        }
    </style>
    """
    
    js = """
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        console.log("Table assets loaded.");
    </script>
    """
    return css, js

def generate_table_html(table_category, csv_data):
    """dd
    Parses CSV string and returns ONLY the <table> HTML structure.
    """
    # Use StringIO to treat the string as a file stream
    f = io.StringIO(csv_data.strip())
    
    # csv.reader handles the complex quoting/newlines automatically
    reader = csv.reader(f)
    
    try:
        headers = next(reader)
    except StopIteration:
        return "<div class='alert alert-warning'>No data found in CSV.</div>"

    # Start building HTML
    html_out = [f'<h3 class="mb-3 text-capitalize">{table_category} Data</h3>']
    html_out.append('<table class="table table-striped table-hover table-bordered table-sm">')
    
    # Table Header
    html_out.append('<thead class="table-dark"><tr>')
    for h in headers:
        html_out.append(f'<th scope="col">{html.escape(h)}</th>')
    html_out.append('</tr></thead>')
    
    # Table Body
    html_out.append('<tbody>')
    for row in reader:
        html_out.append('<tr>')
        for cell in row:
            # Escape HTML to prevent XSS from data content
            safe_cell = html.escape(cell)
            # Add class for truncation if content is long
            cell_class = "data-cell" if len(safe_cell) > 50 else ""
            html_out.append(f'<td class="{cell_class}" title="{safe_cell}">{safe_cell}</td>')
        html_out.append('</tr>')
    html_out.append('</tbody>')
    
    html_out.append('</table>')
    
    return "\n".join(html_out)

if __name__ == "__main__":
    # --- TEMPORARY TESTING SPACE ---
    
    # 1. The Variable (Simulating reading from file)
    raw_csv_data = r'''name,namespace,uid,failed_jobs_history_limit,schedule,starting_deadline_seconds,successful_jobs_history_limit,suspend,concurrency_policy,job_template,last_schedule_time,last_successful_time,active,context_name,source_type,title,tags,generate_name,resource_version,generation,creation_timestamp,deletion_timestamp,deletion_grace_period_seconds,labels,annotations,owner_references,finalizers,path,start_line,end_line,sp_connection_name,sp_ctx,_ctx
kdiff-snapshots,kdiff,ea445e6b-cda3-4b5a-b6c2-e72f635e84c6,2,00 20 * * *,90,5,false,"""Forbid""","{""metadata"":{""creationTimestamp"":null},""spec"":{""template"":{""metadata"":{""creationTimestamp"":null,""labels"":{""app.kubernetes.io/instance"":""kdiff-snapshots"",""app.kubernetes.io/name"":""kdiff""}},""spec"":{""automountServiceAccountToken"":true,""containers"":[{""envFrom"":[{""configMapRef"":{""name"":""kdiff-snapshots-cm-env-vars""}},{""secretRef"":{""name"":""kdiff-snapshots-steampipe-creds""}},{""secretRef"":{""name"":""kdiff-snapshots-secret-env-vars""}}],""image"":""ghcr.io/oguzhan-yilmaz/kdiff-snapshots:latest"",""imagePullPolicy"":""Always"",""name"":""kdiff-snapshots"",""ports"":[{""containerPort"":9193,""name"":""postgres"",""protocol"":""TCP""}],""resources"":{},""securityContext"":{""runAsGroup"":11234,""runAsNonRoot"":true,""runAsUser"":11234},""terminationMessagePath"":""/dev/termination-log"",""terminationMessagePolicy"":""File""}],""dnsPolicy"":""ClusterFirst"",""hostNetwork"":true,""restartPolicy"":""OnFailure"",""schedulerName"":""default-scheduler"",""securityContext"":{""fsGroup"":11234},""serviceAccount"":""kdiff-snapshots"",""serviceAccountName"":""kdiff-snapshots"",""terminationGracePeriodSeconds"":30}}}}",2025-11-06T20:00:00+03:00,,"[{""apiVersion"":""batch/v1"",""kind"":""Job"",""name"":""kdiff-snapshots-29374140"",""namespace"":""kdiff"",""resourceVersion"":""1219308"",""uid"":""5294bd23-ffc8-41e0-baed-36a88ce6c1ce""}]",kind-kinder,deployed,kdiff-snapshots,"{""app.kubernetes.io/instance"":""kdiff-snapshots"",""app.kubernetes.io/managed-by"":""Helm"",""app.kubernetes.io/name"":""kdiff"",""app.kubernetes.io/version"":""0.0.69"",""helm.sh/chart"":""kdiff-0.1.0"",""meta.helm.sh/release-name"":""kdiff-snapshots"",""meta.helm.sh/release-namespace"":""kdiff""}",,1219310,5,2025-10-12T20:43:06+03:00,,,"{""app.kubernetes.io/instance"":""kdiff-snapshots"",""app.kubernetes.io/managed-by"":""Helm"",""app.kubernetes.io/name"":""kdiff"",""app.kubernetes.io/version"":""0.0.69"",""helm.sh/chart"":""kdiff-0.1.0""}","{""meta.helm.sh/release-name"":""kdiff-snapshots"",""meta.helm.sh/release-namespace"":""kdiff""}",,,,,,kubernetes_kind_kinder,"{""connection_name"":""kubernetes_kind_kinder"",""steampipe"":{""sdk_version"":""5.13.1""}}","{""connection_name"":""kubernetes_kind_kinder"",""steampipe"":{""sdk_version"":""5.13.1""}}"
grafana-snapshot-creator,monitoring,b15ae22d-8c36-45c3-86b5-e818817d63c1,1,0 * * * *,,3,false,"""Allow""","{""metadata"":{""creationTimestamp"":null},""spec"":{""template"":{""metadata"":{""creationTimestamp"":null},""spec"":{""containers"":[{""command"":[""sh"",""-c"",""echo \""Creating Grafana snapshot...\""\n\nDASHBOARD_JSON=$(curl -s -H \""Authorization: $GRAFANA_AUTH_HEADER\"" \""$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID\"" | jq .dashboard)\n# DASHBOARD_JSON=$(curl -s \""$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID\"" | jq .dashboard)\necho \""DASHBOARD_UID=$DASHBOARD_UID\""  \necho \""$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID\""\n# echo \""DASHBOARD_JSON=$DASHBOARD_JSON\""  \n# $name should be unique for each snapshot\nSNAPSHOT_PAYLOAD=$(jq -n \\\n  --argjson dashboard \""$DASHBOARD_JSON\"" \\\n  --arg name \""$SNAPSHOT_NAME\"" \\\n  --arg key \""snapshot-bravo-grafana\"" \\\n  '{dashboard: $dashboard, name: $name, expires: 3600, external: true}')\necho \""sending request to create snapshot /api/snapshots...\""\ncurl -s -X POST \""$GRAFANA_URL/api/snapshots\"" \\\n  -H \""Content-Type: application/json\"" \\\n   -H \""Authorization: $GRAFANA_AUTH_HEADER\"" \\\n  -d \""$SNAPSHOT_PAYLOAD\"" | tee /tmp/snapshot-response.json\necho \""SNAPSHOT_PAYLOAD=$SNAPSHOT_PAYLOAD\""\n  \n\necho \""Snapshot created:\""\ncat /tmp/snapshot-response.json\n""],""env"":[{""name"":""GRAFANA_URL"",""value"":""http://kind-prometheus-grafana.monitoring.svc""},{""name"":""DASHBOARD_UID"",""value"":""vkQ0UHxik""},{""name"":""GRAFANA_AUTH_HEADER"",""value"":""Basic YWRtaW46cHJvbS1vcGVyYXRvcg==""},{""name"":""SNAPSHOT_NAME"",""value"":""CoreDNS Automated Snapshot2233""}],""image"":""ganeshpl/alpine-jq"",""imagePullPolicy"":""IfNotPresent"",""name"":""grafana-snapshot"",""resources"":{},""terminationMessagePath"":""/dev/termination-log"",""terminationMessagePolicy"":""File""}],""dnsPolicy"":""ClusterFirst"",""restartPolicy"":""OnFailure"",""schedulerName"":""default-scheduler"",""securityContext"":{},""terminationGracePeriodSeconds"":30}}}}",2025-11-21T15:00:00+03:00,2025-11-21T15:15:36+03:00,,kind-kinder,deployed,grafana-snapshot-creator,"{""kubectl.kubernetes.io/last-applied-configuration"":""{\""apiVersion\"":\""batch/v1\"",\""kind\"":\""CronJob\"",\""metadata\"":{\""annotations\"":{},\""name\"":\""grafana-snapshot-creator\"",\""namespace\"":\""monitoring\""},\""spec\"":{\""jobTemplate\"":{\""spec\"":{\""template\"":{\""spec\"":{\""containers\"":[{\""command\"":[\""sh\"",\""-c\"",\""echo \\\""Creating Grafana snapshot...\\\""\\n\\nDASHBOARD_JSON=$(curl -s -H \\\""Authorization: $GRAFANA_AUTH_HEADER\\\"" \\\""$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID\\\"" | jq .dashboard)\\n# DASHBOARD_JSON=$(curl -s \\\""$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID\\\"" | jq .dashboard)\\necho \\\""DASHBOARD_UID=$DASHBOARD_UID\\\""  \\necho \\\""$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID\\\""\\n# echo \\\""DASHBOARD_JSON=$DASHBOARD_JSON\\\""  \\n# $name should be unique for each snapshot\\nSNAPSHOT_PAYLOAD=$(jq -n \\\\\\n  --argjson dashboard \\\""$DASHBOARD_JSON\\\"" \\\\\\n  --arg name \\\""$SNAPSHOT_NAME\\\"" \\\\\\n  --arg key \\\""snapshot-bravo-grafana\\\"" \\\\\\n  '{dashboard: $dashboard, name: $name, expires: 3600, external: true}')\\necho \\\""sending request to create snapshot /api/snapshots...\\\""\\ncurl -s -X POST \\\""$GRAFANA_URL/api/snapshots\\\"" \\\\\\n  -H \\\""Content-Type: application/json\\\"" \\\\\\n   -H \\\""Authorization: $GRAFANA_AUTH_HEADER\\\"" \\\\\\n  -d \\\""$SNAPSHOT_PAYLOAD\\\"" | tee /tmp/snapshot-response.json\\necho \\\""SNAPSHOT_PAYLOAD=$SNAPSHOT_PAYLOAD\\\""\\n  \\n\\necho \\\""Snapshot created:\\\""\\ncat /tmp/snapshot-response.json\\n\""],\""env\"":[{\""name\"":\""GRAFANA_URL\"",\""value\"":\""http://kind-prometheus-grafana.monitoring.svc\""},{\""name\"":\""DASHBOARD_UID\"",\""value\"":\""vkQ0UHxik\""},{\""name\"":\""GRAFANA_AUTH_HEADER\"",\""value\"":\""Basic YWRtaW46cHJvbS1vcGVyYXRvcg==\""},{\""name\"":\""SNAPSHOT_NAME\"",\""value\"":\""CoreDNS Automated Snapshot2233\""}],\""image\"":\""ganeshpl/alpine-jq\"",\""name\"":\""grafana-snapshot\""}],\""restartPolicy\"":\""OnFailure\""}}}},\""schedule\"":\""0 * * * *\""}}\n""}",,2023788,18,2025-10-28T00:38:28+03:00,,,,"{""kubectl.kubernetes.io/last-applied-configuration"":""{\""apiVersion\"":\""batch/v1\"",\""kind\"":\""CronJob\"",\""metadata\"":{\""annotations\"":{},\""name\"":\""grafana-snapshot-creator\"",\""namespace\"":\""monitoring\""},\""spec\"":{\""jobTemplate\"":{\""spec\"":{\""template\"":{\""spec\"":{\""containers\"":[{\""command\"":[\""sh\"",\""-c\"",\""echo \\\""Creating Grafana snapshot...\\\""\\n\\nDASHBOARD_JSON=$(curl -s -H \\\""Authorization: $GRAFANA_AUTH_HEADER\\\"" \\\""$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID\\\"" | jq .dashboard)\\n# DASHBOARD_JSON=$(curl -s \\\""$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID\\\"" | jq .dashboard)\\necho \\\""DASHBOARD_UID=$DASHBOARD_UID\\\""  \\necho \\\""$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID\\\""\\n# echo \\\""DASHBOARD_JSON=$DASHBOARD_JSON\\\""  \\n# $name should be unique for each snapshot\\nSNAPSHOT_PAYLOAD=$(jq -n \\\\\\n  --argjson dashboard \\\""$DASHBOARD_JSON\\\"" \\\\\\n  --arg name \\\""$SNAPSHOT_NAME\\\"" \\\\\\n  --arg key \\\""snapshot-bravo-grafana\\\"" \\\\\\n  '{dashboard: $dashboard, name: $name, expires: 3600, external: true}')\\necho \\\""sending request to create snapshot /api/snapshots...\\\""\\ncurl -s -X POST \\\""$GRAFANA_URL/api/snapshots\\\"" \\\\\\n  -H \\\""Content-Type: application/json\\\"" \\\\\\n   -H \\\""Authorization: $GRAFANA_AUTH_HEADER\\\"" \\\\\\n  -d \\\""$SNAPSHOT_PAYLOAD\\\"" | tee /tmp/snapshot-response.json\\necho \\\""SNAPSHOT_PAYLOAD=$SNAPSHOT_PAYLOAD\\\""\\n  \\n\\necho \\\""Snapshot created:\\\""\\ncat /tmp/snapshot-response.json\\n\""],\""env\"":[{\""name\"":\""GRAFANA_URL\"",\""value\"":\""http://kind-prometheus-grafana.monitoring.svc\""},{\""name\"":\""DASHBOARD_UID\"",\""value\"":\""vkQ0UHxik\""},{\""name\"":\""GRAFANA_AUTH_HEADER\"",\""value\"":\""Basic YWRtaW46cHJvbS1vcGVyYXRvcg==\""},{\""name\"":\""SNAPSHOT_NAME\"",\""value\"":\""CoreDNS Automated Snapshot2233\""}],\""image\"":\""ganeshpl/alpine-jq\"",\""name\"":\""grafana-snapshot\""}],\""restartPolicy\"":\""OnFailure\""}}}},\""schedule\"":\""0 * * * *\""}}\n""}",,,,,,kubernetes_kind_kinder,"{""connection_name"":""kubernetes_kind_kinder"",""steampipe"":{""sdk_version"":""5.13.1""}}","{""connection_name"":""kubernetes_kind_kinder"",""steampipe"":{""sdk_version"":""5.13.1""}}"
'''
    
    # 2. Get the Assets
    page_css, page_js = get_page_assets()
    
    # 3. Generate the Table
    table_html = generate_table_html("Kubernetes CronJobs", raw_csv_data)
    
    # 4. Construct Final HTML Template
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
    
    # 5. Save to file
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(full_html)
        
    print("Success: 'report.html' has been generated.")