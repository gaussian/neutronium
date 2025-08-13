

def truncate_strings(obj, max_len):
    """
    Recursively truncate strings within nested structures.

    - If obj is a str, truncate to max_len and add "..." if truncated.
    - If obj is a dict, truncate its values recursively.
    - If obj is a list or tuple, truncate its elements recursively.
    - Otherwise, convert obj to str and truncate if needed.
    """
    if isinstance(obj, str):
        return obj if len(obj) <= max_len else obj[:max_len] + "..."
    if isinstance(obj, dict):
        return {k: truncate_strings(v, max_len) for k, v in obj.items()}
    if isinstance(obj, list):
        return [truncate_strings(item, max_len) for item in obj]
    if isinstance(obj, tuple):
        return tuple(truncate_strings(item, max_len) for item in obj)
    # Fallback for other types
    s = str(obj)
    return s if len(s) <= max_len else s[:max_len] + "..."


def print_trunc(obj, max_len=50):
    """
    Print the object with all strings truncated to max_len.

    Nested structures (dicts, lists, tuples) will have their strings truncated recursively.
    Uses pprint for nicer formatting of nested structures.
    """
    from pprint import pprint

    truncated = truncate_strings(obj, max_len)
    if isinstance(truncated, (dict, list, tuple)):
        pprint(truncated)
    else:
        print(truncated)


# Example usage:
# my_data = {
#     "message": "This is a very long message that will be truncated.",
#     "items": ["short", "a very very long list item that needs truncation"],
#     "nested": {"key": "another lengthy string that exceeds the limit"}
# }
# print_trunc(my_data, max_len=20)
