# Kdiff UI

## Running the application

```bash
uv run streamlit run mainpage.py
```


```bash
❯ jq '.[].rows[].data_type' tables.structure.json | sort | uniq
"bigint"
"boolean"
"cidr"
"inet"
"jsonb"
"text"
"timestamp with time zone"
```