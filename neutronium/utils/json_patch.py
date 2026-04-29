
from typing import Any

JsonObj = dict[str, Any]


def deep_merge(dst: JsonObj, src: JsonObj) -> JsonObj:
    """
    Recursively merge ``src`` into ``dst`` (dicts only). Lists/scalars in
    ``src`` replace whatever is at the same key in ``dst``. Mutates and
    returns ``dst``.
    """
    for k, v in src.items():
        if k in dst and isinstance(dst[k], dict) and isinstance(v, dict):
            deep_merge(dst[k], v)
        else:
            dst[k] = v
    return dst


def json_pointer_delete(doc: Any, pointer: str) -> None:
    """
    Delete the value at ``pointer`` from ``doc`` if it exists. JSON Pointer
    per RFC 6901, with ``~0`` => ``~``, ``~1`` => ``/`` unescaping. No
    error if the path is missing; silently no-ops.
    """
    # Empty string or "/" alone doesn't reference a valid sub-element.
    if pointer == "" or pointer == "/":
        return

    parts = pointer.split("/")
    # First element should be "", because pointers start with "/"
    if not parts or parts[0] != "":
        return

    # Walk to parent of target
    cur = doc
    for token in parts[1:-1]:
        key = _unescape(token)
        if isinstance(cur, dict):
            if key not in cur:
                return
            cur = cur[key]
        elif isinstance(cur, list):
            idx = _parse_array_index(key, cur)
            if idx is None:
                return
            cur = cur[idx]
        else:
            return

    # Delete the leaf
    leaf_token = _unescape(parts[-1])
    if isinstance(cur, dict):
        cur.pop(leaf_token, None)
    elif isinstance(cur, list):
        idx = _parse_array_index(leaf_token, cur)
        if idx is not None:
            del cur[idx]


def _parse_array_index(key: str, array: list) -> int | None:
    """
    Parse ``key`` as an array index and validate it's within bounds.
    Returns the index if valid, ``None`` otherwise.
    """
    try:
        idx = int(key)
    except ValueError:
        return None
    if idx < 0 or idx >= len(array):
        return None
    return idx


def _unescape(token: str) -> str:
    """JSON Pointer unescaping: ``~1`` -> ``/``, ``~0`` -> ``~``."""
    return token.replace("~1", "/").replace("~0", "~")
