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


# --- Dynamic dataclass table builder ---
def build_table_classes(schema: Dict[str, Any]) -> Dict[str, Type]:
    """Build a dataclass for each table in the schema."""
    classes = {}

    for table_name, table_def in schema.items():
        fields_spec = []
        for col in table_def["rows"]:
            col_name = col["column_name"]
            sql_type = col["data_type"]
            py_type = map_data_type(sql_type)
            fields_spec.append((col_name, py_type, field(default=None)))

        TableClass = make_dataclass(
            # table_name.capitalize(),  # class name
            table_name,  # class name
            fields_spec,
            frozen=False,
            # repr=True
        )
        
        # Add helper for automatic type conversion on init
        orig_init = TableClass.__init__

        def __init__(self, **kwargs):
            hints = get_type_hints(self.__class__)
            converted = {}
            for key, value in kwargs.items():
                if key in hints:
                    converted[key] = convert_value(value, hints[key])
                else:
                    converted[key] = value
            orig_init(self, **converted)

        TableClass.__init__ = __init__

        classes[table_name] = TableClass

    return classes


# --- Example usage ---

def get_scheme_json_file(schema_json_filepath: Path):
    with open(f"{schema_json_filepath}", 'r') as ff:
        # schema = json.load(ff)
        content = ff.read()
    return content

def get_data_tables(schema_json_filepath: Path):
    schema_json = get_scheme_json_file(schema_json_filepath)
    schema = json.loads(schema_json)
    # print(json.dumps(schema, indent=2) )
    tables = build_table_classes(schema)
    return tables


def get_data_tables_from_multiple_schemas(schema_json_filepath_list: List[Path]) -> Dict:
    r = {}
    for schema_json_filepath in schema_json_filepath_list:
        schema_json = get_scheme_json_file(schema_json_filepath)
        schema = json.loads(schema_json)
        # print(json.dumps(schema, indent=2) )
        tables = build_table_classes(schema)
        r.update(tables)
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
    # """
    tables = get_data_tables('/Users/ogair/Projects/kdiff/tables.structure.json')
    print(json.dumps(tables, indent=2, default=str))
    # # Use it dynamically
    # ClusterRole = tables["kubernetes_cluster_role"]
    t = tables['kubernetes_pod']
    print(dir(t))
    print('----')
    print(t.__class__)
    # print(t.__dict__)
