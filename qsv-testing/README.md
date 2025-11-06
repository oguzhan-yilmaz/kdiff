qsv diff --drop-equal-fields --key namespace,name --sort-columns namespace,name /Users/ogair/tmp-kdiff-snapshots-sync/snps/kdiff-snapshot-2025-11-03--23-17/kubernetes_role.csv /Users/ogair/tmp-kdiff-snapshots-sync/snps/kdiff-snapshot-2025-11-03--23-54/kubernetes_role.csv

qsv diff --drop-equal-fields --key namespace,name --sort-columns namespace,name 
qsv diff --drop-equal-fields --key namespace,name --sort-columns namespace,name


http://localhost:8501/queryparam?snapshot-a=kdiff-snapshot-2025-11-04--22-39&snapshot-b=kdiff-snapshot-2025-11-05--22-14
http://localhost:8501/queryparam?snapshot-a=kdiff-snapshot-2025-11-03--23-59&snapshot-b=kdiff-snapshot-2025-11-04--22-39



export STEAMPIPE_CACHE=false 



http://localhost:8501/queryparam?snapshot-a=&snapshot-b=


http://localhost:8501/queryparam?snapshot-a=kdiff-snapshot-2025-11-06--15-04&snapshot-b=kdiff-snapshot-2025-11-06--20-14

/

qsv diff /Users/ogair/tmp-kdiff-snapshots-sync/snps/kdiff-snapshot-2025-11-06--15-04/kubernetes_pod.csv /Users/ogair/tmp-kdiff-snapshots-sync/snps/kdiff-snapshot-2025-11-06--15-08/kubernetes_pod.csv 



cat /Users/ogair/tmp-kdiff-snapshots-sync/snps/kdiff-snapshot-2025-11-06--15-04/kubernetes_pod.csv
code /Users/ogair/tmp-kdiff-snapshots-sync/snps/kdiff-snapshot-2025-11-06--15-08/kubernetes_pod.csv 