from typing import Any

class SchemaError(ValueError):
    pass

TYPE_NAMES = {"TEXT", "NUMBER", "INTEGER", "BOOLEAN", "CONFIDENCE", "CLASSIFICATION"}

def validate_value(type_name: str, value: Any, field: str = "value") -> None:
    if type_name == "TEXT" and not isinstance(value, str):
        raise SchemaError(f"{field}: expected TEXT, got {type(value).__name__}")
    if type_name in {"NUMBER", "CONFIDENCE"} and (not isinstance(value, (int, float)) or isinstance(value, bool)):
        raise SchemaError(f"{field}: expected NUMBER, got {type(value).__name__}")
    if type_name == "CONFIDENCE" and not 0 <= float(value) <= 1:
        raise SchemaError(f"{field}: confidence must be between 0 and 1")
    if type_name == "INTEGER" and (not isinstance(value, int) or isinstance(value, bool)):
        raise SchemaError(f"{field}: expected INTEGER, got {type(value).__name__}")
    if type_name == "BOOLEAN" and not isinstance(value, bool):
        raise SchemaError(f"{field}: expected BOOLEAN, got {type(value).__name__}")
    if type_name in {"CLASSIFICATION"} and not isinstance(value, str):
        raise SchemaError(f"{field}: expected CLASSIFICATION text, got {type(value).__name__}")

def validate_output(schema: dict[str, str], output: dict[str, Any], categories: list[str] | None = None) -> dict[str, Any]:
    for field, type_name in schema.items():
        if field not in output:
            raise SchemaError(f"missing required cognitive output: {field}")
        validate_value(type_name, output[field], field)
    if categories and "category" in output and output["category"] not in categories:
        raise SchemaError(f"category '{output['category']}' is not one of {categories}")
    return output
