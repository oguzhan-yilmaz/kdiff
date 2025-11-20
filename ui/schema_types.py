import json
from dataclasses import dataclass, field, make_dataclass
from datetime import datetime
from typing import Any, Dict, List, Type, Optional, get_type_hints
import dateutil.parser  # part of python-dateutil, very light dependency
from pathlib import Path
# --- Type mapping function ---

def map_data_type(sql_type: str):
    """Map SQL data types to Python types."""
    sql_type = sql_type.lower()
    if sql_type in {"text", "varchar", "character varying"}:
        return str
    elif sql_type in {"bigint", "integer", "int"}:
        return int
    elif sql_type in {"json", "jsonb"}:
        return dict
    elif sql_type.startswith("timestamp"):
        return datetime
    elif sql_type in {"boolean", "bool"}:
        return bool
    else:
        return Any

def map_data_type_opt(sql_type: str):
    """Map SQL data types to Python types."""
    sql_type = sql_type.lower()
    if sql_type in {"text", "varchar", "character varying"}:
        return Optional[str]
    elif sql_type in {"bigint", "integer", "int"}:
        return Optional[int]
    elif sql_type in {"json", "jsonb"}:
        return Optional[dict]
    elif sql_type.startswith("timestamp"):
        return Optional[datetime]
    elif sql_type in {"boolean", "bool"}:
        return Optional[bool]
    else:
        return Optional[Any]

# --- Conversion utility ---

def convert_value(value, py_type):
    """Convert raw value from input into expected Python type."""
    if value is None:
        return None
    origin_type = getattr(py_type, "__origin__", None)

    if py_type in (str, Optional[str]) or origin_type is str:
        return str(value)
    elif py_type in (int, Optional[int]) or origin_type is int:
        return int(value)
    elif py_type in (bool, Optional[bool]) or origin_type is bool:
        if isinstance(value, str):
            return value.lower() in {"true", "1", "t", "yes"}
        return bool(value)
    elif py_type in (dict, Optional[dict]) or origin_type is dict:
        if isinstance(value, str):
            return json.loads(value)
        return dict(value)
    elif py_type in (datetime, Optional[datetime]) or origin_type is datetime:
        if isinstance(value, datetime):
            return value
        return dateutil.parser.parse(value)
    else:
        return value


# --- Example usage ---

def get_table_data_types(schema_json_filepath: Path):
    with open(f"{schema_json_filepath}", 'r') as ff:
        schema_json = json.load(ff)
    
    r = {}
    for table_name, t_conf in schema_json.items():
        v ={
            x['column_name']: x['data_type']
            for x in t_conf['rows']
        }
        r[table_name] = v
    return r


if __name__ == "__main__":

    # schema_json = """
    # {
    #   "kubernetes_cluster_role": {
    #     "rows": [
    #       {"column_name": "name", "data_type": "text", "is_nullable": "YES"},
    #       {"column_name": "generation", "data_type": "bigint", "is_nullable": "YES"},
    #       {"column_name": "rules", "data_type": "jsonb", "is_nullable": "YES"}
    #     ]
    #   }
    # }

        
    
    # print(json.dumps(r, indent=2, default=str))

    # # Use it dynamically
    # ClusterRole = tables["kubernetes_cluster_role"]
    # t = tables['kubernetes_pod']
    # print(dir(t))
    # print('----')
    # print(t.__class__)
    # print(t.__dict__)
    pass