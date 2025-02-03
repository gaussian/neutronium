from typing import Any, Optional


def schema_to_default_dict(schema: dict):
    """
    Convert a schema to a dictionary with default values.

    Example:
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "default": 18},
            "hobbies": {"type": "array", "items": {"type": "string"}}
        }
    }
    
    Output: {'name': None, 'age': 18, 'hobbies': []}
    """
    result = {}
    for key, value in schema["properties"].items():
        if "default" in value:
            result[key] = value["default"]
        elif value["type"] == "array":
            result[key] = []
        elif value["type"] == "object":
            result[key] = {}
        else:
            result[key] = None
    return result
