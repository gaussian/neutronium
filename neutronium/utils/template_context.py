
"""
Pure Python utilities for template variable extraction and context building.
No Django dependencies - can be tested without Django setup.

For Django-dependent email template utilities, see neutron.messaging.template_context.
"""

import copy
import re


# Django built-in template tags that should not be treated as variables
TEMPLATE_BUILTINS = {
    "block",
    "endblock",
    "extends",
    "include",
    "load",
    "if",
    "endif",
    "for",
    "endfor",
    "with",
    "endwith",
    "autoescape",
    "endautoescape",
    "blocktranslate",
    "endblocktranslate",
    "blocktrans",
    "endblocktrans",
    "trans",
    "now",
    "csrf_token",
    "url",
    "static",
    "forloop",
}

# Variables that are always provided by Django/allauth framework
# and don't need to be in extra_context or matched between templates
FRAMEWORK_VARS = {
    "current_site",
    "site_domain",
    "user",
    "username",
    "user_display",
    "email",
    "app_name",
    "root_url",
}

# Number of sample items to generate in dicts and lists
SAMPLE_ITEMS_COUNT = 2


def extract_template_variables_full(template_content: str) -> dict[str, str | None]:
    """
    Extract full variable paths from {{ var.path.here }} and {% for x in var.path %} patterns.
    Resolves loop variables back to their source paths with proper scope handling.

    Returns dict mapping paths to their iteration type:
    - None: scalar variable ({{ var }})
    - "items": dict iteration ({% for k, v in var.items %})
    - "values"/"keys": dict iteration
    - "list": list iteration ({% for x in var %})

    For nested loops like:
        {% for group_name, records in section_data.groupings.items %}
        {% for record in records %}
        {{ record.body }}

    This resolves record.body -> section_data.groupings.*.0.body
    (where * represents dict value and 0 represents list item)

    Handles same variable name in different scopes correctly:
        {% for item in list1 %}{{ item.prop1 }}{% endfor %}
        {% for item in list2 %}{{ item.prop2 }}{% endfor %}
    -> list1.0.prop1 and list2.0.prop2 (not mixed up)
    """
    result: dict[str, str | None] = {}

    # Build scope ranges for each for-loop block
    # Each scope is: (start_pos, end_pos, var_name, source_path, is_value, method)
    scopes = _build_for_loop_scopes(template_content)

    # Process each scope to record collection paths
    for scope in scopes:
        _start, _end, _var_names, resolved_source, _is_values, method = scope
        # Record the collection path with its iteration type
        root = resolved_source.split(".")[0]
        if root not in TEMPLATE_BUILTINS:
            if method:
                result[resolved_source] = method
            elif resolved_source not in result or result[resolved_source] is None:
                result[resolved_source] = "list"

    # Build scope ranges for {% with %} blocks
    with_scopes = _build_with_scopes(template_content, scopes)

    # Extract variables from {% if var %} conditions with scope awareness
    if_pattern = r"\{%\s*if\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)*)"
    for match in re.finditer(if_pattern, template_content):
        var_path = match.group(1)
        pos = match.start()
        root = var_path.split(".")[0]
        if root in TEMPLATE_BUILTINS:
            continue
        loop_var_sources = _get_scope_at_position(pos, scopes, with_scopes)
        resolved_path = _resolve_loop_variable(var_path, loop_var_sources)
        if resolved_path:
            if resolved_path not in result:
                result[resolved_path] = None
        elif var_path not in result:
            result[var_path] = None

    # Extract {{ variable.path }} with scope awareness
    var_pattern = r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)*)"
    for match in re.finditer(var_pattern, template_content):
        var_path = match.group(1)
        pos = match.start()
        root = var_path.split(".")[0]
        if root in TEMPLATE_BUILTINS:
            continue

        loop_var_sources = _get_scope_at_position(pos, scopes, with_scopes)
        resolved_path = _resolve_loop_variable(var_path, loop_var_sources)
        if resolved_path:
            if resolved_path not in result:
                result[resolved_path] = None
        elif var_path not in result:
            result[var_path] = None

    return result


def _build_for_loop_scopes(
    template_content: str,
) -> list[tuple[int, int, list[str], str, list[bool], str | None]]:
    """
    Build a list of for-loop scopes with their positions and variable mappings.

    Returns list of tuples:
        (start_pos, end_pos, var_names, resolved_source, is_values, method)

    Where:
        - start_pos: position after {% for %}
        - end_pos: position of {% endfor %}
        - var_names: list of loop variable names (1 or 2 for .items)
        - resolved_source: the resolved source path
        - is_values: list of bools indicating if each var is a value (vs key)
        - method: "items", "values", "keys", or None for list iteration
    """
    scopes: list[tuple[int, int, list[str], str, list[bool], str | None]] = []

    # Find all {% for %} tags with their positions
    # Pattern for dict iteration: {% for x, y in path.items %}
    for_dict_pattern = r"\{%\s*for\s+(\w+)(?:\s*,\s*(\w+))?\s+in\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)*)\.(items|values|keys)\s*%\}"

    # Pattern for list iteration: {% for x in path %}
    for_list_pattern = r"\{%\s*for\s+(\w+)\s+in\s+([a-zA-Z_][a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*)\s*%\}"

    # Collect all for-loop starts with their info
    for_starts: list[tuple[int, int, list[str], str, list[bool], str | None]] = []

    for match in re.finditer(for_dict_pattern, template_content):
        var1, var2, source_path, method = match.groups()
        start_pos = match.end()
        if var2:
            var_names = [var1, var2]
            is_values = [False, True]  # var1 is key, var2 is value
        else:
            var_names = [var1]
            is_values = [True]
        for_starts.append((match.start(), start_pos, var_names, source_path, is_values, method))

    for match in re.finditer(for_list_pattern, template_content):
        var1, source_path = match.groups()
        # Skip if this is actually a dict pattern (ends with .items/.values/.keys)
        if source_path.endswith((".items", ".values", ".keys")):
            continue
        start_pos = match.end()
        for_starts.append((match.start(), start_pos, [var1], source_path, [True], None))

    # Sort by start position
    for_starts.sort(key=lambda x: x[0])

    # Find matching {% endfor %} for each {% for %}
    endfor_pattern = r"\{%\s*endfor\s*%\}"
    endfor_positions = [m.start() for m in re.finditer(endfor_pattern, template_content)]

    # Match for-loops with endfor using a stack
    # Stack contains tuples with RESOLVED source paths
    stack: list[tuple[int, int, list[str], str, list[bool], str | None]] = []
    for_idx = 0
    endfor_idx = 0

    # Process in order of position
    while for_idx < len(for_starts) or (stack and endfor_idx < len(endfor_positions)):
        # Get next for and endfor positions
        next_for_pos = for_starts[for_idx][0] if for_idx < len(for_starts) else float("inf")
        next_endfor_pos = endfor_positions[endfor_idx] if endfor_idx < len(endfor_positions) else float("inf")

        if next_for_pos < next_endfor_pos:
            # Push this for-loop onto stack, resolving source path using parent scopes on stack
            tag_start, start_pos, var_names, source_path, is_values, method = for_starts[for_idx]

            # Build loop_var_sources from parent loops still on the stack
            loop_var_sources: dict[str, tuple[str, bool]] = {}
            for _s_tag_start, _s_start_pos, s_var_names, s_resolved_source, s_is_values, _s_method in stack:
                for var_name, is_value in zip(s_var_names, s_is_values):
                    loop_var_sources[var_name] = (s_resolved_source, is_value)

            # Resolve source_path if it starts with a loop variable
            resolved_source = source_path
            source_root = source_path.split(".")[0]
            if source_root in loop_var_sources:
                resolved = _resolve_loop_variable(source_path, loop_var_sources)
                if resolved:
                    resolved_source = resolved

            # Push with resolved source
            stack.append((tag_start, start_pos, var_names, resolved_source, is_values, method))
            for_idx += 1
        else:
            # Pop from stack and create scope
            if stack:
                tag_start, start_pos, var_names, resolved_source, is_values, method = stack.pop()
                end_pos = endfor_positions[endfor_idx]
                scopes.append((start_pos, end_pos, var_names, resolved_source, is_values, method))
            endfor_idx += 1

    return scopes


def _build_with_scopes(
    template_content: str,
    for_scopes: list[tuple[int, int, list[str], str, list[bool], str | None]],
) -> list[tuple[int, int, str, str]]:
    """
    Build a list of {% with %} scopes with their positions and variable mappings.

    Returns list of tuples: (start_pos, end_pos, var_name, resolved_path)
    """
    scopes: list[tuple[int, int, str, str]] = []

    with_pattern = r"\{%\s*with\s+(\w+)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)*)\s*%\}"
    endwith_pattern = r"\{%\s*endwith\s*%\}"

    with_starts: list[tuple[int, int, str, str]] = []
    for match in re.finditer(with_pattern, template_content):
        var_name, expr = match.groups()
        with_starts.append((match.start(), match.end(), var_name, expr))

    with_starts.sort(key=lambda x: x[0])

    endwith_positions = [m.start() for m in re.finditer(endwith_pattern, template_content)]

    # Match with-blocks with endwith using a stack
    stack: list[tuple[int, int, str, str]] = []
    with_idx = 0
    endwith_idx = 0

    while with_idx < len(with_starts) or (stack and endwith_idx < len(endwith_positions)):
        next_with_pos = with_starts[with_idx][0] if with_idx < len(with_starts) else float("inf")
        next_endwith_pos = endwith_positions[endwith_idx] if endwith_idx < len(endwith_positions) else float("inf")

        if next_with_pos < next_endwith_pos:
            stack.append(with_starts[with_idx])
            with_idx += 1
        else:
            if stack:
                tag_start, start_pos, var_name, expr = stack.pop()
                end_pos = endwith_positions[endwith_idx]

                # Resolve expr using scopes at this position
                loop_var_sources = _get_scope_at_position(tag_start, for_scopes, scopes)
                expr_root = expr.split(".")[0]
                if expr_root in loop_var_sources:
                    resolved_expr = _resolve_loop_variable(expr, loop_var_sources)
                    if resolved_expr:
                        scopes.append((start_pos, end_pos, var_name, resolved_expr))
                    else:
                        scopes.append((start_pos, end_pos, var_name, expr))
                else:
                    scopes.append((start_pos, end_pos, var_name, expr))
            endwith_idx += 1

    return scopes


def _get_scope_at_position(
    pos: int,
    for_scopes: list[tuple[int, int, list[str], str, list[bool], str | None]],
    with_scopes: list[tuple[int, int, str, str]],
) -> dict[str, tuple[str, bool]]:
    """
    Get the loop_var_sources dict valid at a given position.

    Returns dict mapping var_name -> (source_path, is_value)
    """
    loop_var_sources: dict[str, tuple[str, bool]] = {}

    # Add variables from for-loops that contain this position
    for start, end, var_names, resolved_source, is_values, _method in for_scopes:
        if start <= pos < end:
            for var_name, is_value in zip(var_names, is_values):
                loop_var_sources[var_name] = (resolved_source, is_value)

    # Add variables from with-blocks that contain this position
    for start, end, var_name, resolved_path in with_scopes:
        if start <= pos < end:
            loop_var_sources[var_name] = (resolved_path, False)

    return loop_var_sources


def _resolve_loop_variable(
    path: str, loop_var_sources: dict[str, tuple[str, bool]]
) -> str | None:
    """
    Resolve a path that starts with a loop variable to its full context path.

    For example:
        path = "record.body"
        loop_var_sources = {"record": ("records", True), "records": ("section_data.groupings", True)}

    Returns: "section_data.groupings.0.body"
    (where 0 represents list item placeholder)

    The is_loop_item flag indicates if we should add .0 (True for loop items, False for with assignments).
    """
    parts = path.split(".")
    root = parts[0]

    if root not in loop_var_sources:
        return None

    # Build resolved path by following the chain
    source_path, is_loop_item = loop_var_sources[root]
    suffix = ".".join(parts[1:]) if len(parts) > 1 else ""

    # Check if source is also a loop variable
    source_root = source_path.split(".")[0]
    if source_root in loop_var_sources:
        # Recursively resolve
        inner_resolved = _resolve_loop_variable(source_path, loop_var_sources)
        if inner_resolved:
            source_path = inner_resolved

    # For loop items, append .0 marker. For with assignments, use the path directly.
    if is_loop_item:
        if suffix:
            return f"{source_path}.0.{suffix}"
        else:
            return f"{source_path}.0"
    else:
        if suffix:
            return f"{source_path}.{suffix}"
        else:
            return source_path


def generate_fake_value(
    full_path: str, iteration_type: str | None = None
) -> str | dict | list:
    """
    Generate appropriate fake value based on full variable path.
    Examines both the full path and the final part to determine type.

    If iteration_type is set, returns a dict or list structure:
    - "items": {"Sample Key": {}}
    - "values"/"keys"/"list": [{}]
    """
    # Handle iteration types - return structures instead of scalars
    if iteration_type == "items":
        return {"Sample Group": [{}]}
    if iteration_type in ("values", "keys", "list"):
        return [{}]

    path_lower = full_path.lower()
    final_part = full_path.split(".")[-1]
    final_lower = final_part.lower()

    # URL patterns
    if "url" in path_lower or final_part == "activate_url":
        return "https://example.com/path/abc123"

    # Email patterns
    if final_lower == "deleted_email":
        return "deleted@example.com"
    if final_lower == "from_email":
        return "old@example.com"
    if final_lower == "to_email":
        return "new@example.com"
    if "email" in path_lower:
        return "user@example.com"

    # Code patterns
    if final_lower == "code":
        return "123456"

    # Name patterns
    if final_lower == "user_display":
        return "Test User"
    if "name" in final_lower:
        return "Sample Name"

    # Domain patterns
    if final_lower == "site_domain" or final_lower == "domain":
        return "example.com"

    # Content patterns
    if final_lower == "subject":
        return "Test Subject"
    if final_lower == "body":
        return "Test email body content."
    if final_lower == "custom_body":
        return "Custom message content here."

    # ID patterns
    if "id" in final_lower:
        return "12345"

    # Default
    return f"sample_{final_part}"


def _generate_sample_dict_key(coll_path: str, index: int = 1) -> str:
    """
    Generate a readable sample key name for a dict based on its path.

    Examples:
        "record_groups", 1 -> "Sample Record Group 1"
        "record_data.sections", 2 -> "Sample Section 2"
        "section_data.groupings", 3 -> "Sample Grouping 3"
    """
    # Get the last part of the path (the dict name)
    final_part = coll_path.split(".")[-1]

    # Convert snake_case to Title Case and singularize common patterns
    words = final_part.replace("_", " ").split()

    # Singularize last word if it ends in 's' (simple heuristic)
    if words and words[-1].endswith("s") and len(words[-1]) > 1:
        words[-1] = words[-1][:-1]

    # Title case each word
    title_words = [w.capitalize() for w in words]

    return "Sample " + " ".join(title_words) + f" {index}"


def build_nested_context(variable_paths: dict[str, str | None]) -> dict:
    """
    Convert variable paths like 'user.email', 'items.0.name' into nested structure.

    Args:
        variable_paths: Dict mapping paths to iteration types (None for scalars)

    Examples:
        {'user.email': None} -> {'user': {'email': 'user@example.com'}}
        {'items.0.name': None} -> {'items': [{'name': 'Sample Name'}]}
        {'data.groupings': 'items'} -> {'data': {'groupings': {'Sample Group': [{}]}}}

    For nested iterations:
        {'section_data.groupings': 'items', 'section_data.groupings.0.0.body': None}
        -> {'section_data': {'groupings': {'Sample Group': [{'body': 'Test email...'}]}}}
    """
    result: dict = {}

    # Step 1: Identify collection paths (with iteration types) sorted by length
    # Longer paths first so nested collections are processed before their parents
    collection_paths: list[tuple[str, str]] = []
    for path, iteration_type in variable_paths.items():
        parts = path.split(".")
        if parts[0] in FRAMEWORK_VARS:
            continue
        if iteration_type is not None:
            collection_paths.append((path, iteration_type))

    # Sort by path length descending (process deepest collections first)
    collection_paths.sort(key=lambda x: len(x[0]), reverse=True)

    # Track which paths have been handled as inner properties
    handled_paths: set[str] = set()

    # Step 2: For each collection, find its inner properties (leaf paths only)
    inner_properties: dict[str, list[tuple[str, str]]] = {}

    for coll_path, _ in collection_paths:
        props = []
        for path, iter_type in variable_paths.items():
            if path.startswith(coll_path + ".") and iter_type is None:
                suffix = path[len(coll_path) + 1 :]
                # Strip leading numeric indices
                property_parts = suffix.split(".")
                while property_parts and property_parts[0].isdigit():
                    property_parts.pop(0)
                if property_parts:
                    property_path = ".".join(property_parts)
                    props.append((property_path, path))

        # Filter to leaf properties only
        leaf_props = []
        for prop_path, full_path in props:
            is_prefix = any(
                other_path.startswith(prop_path + ".")
                for other_path, _ in props
                if other_path != prop_path
            )
            if not is_prefix:
                leaf_props.append((prop_path, full_path))
                handled_paths.add(full_path)

        inner_properties[coll_path] = leaf_props

    # Step 3: Build collection structures (process in order: deepest first)
    # This map holds built structures for nested collections
    built_collections: dict[str, dict | list] = {}

    for coll_path, iteration_type in collection_paths:
        parts = coll_path.split(".")

        # Build the inner item template
        inner_item: dict = {}

        # Add leaf properties
        for prop_path, full_path in inner_properties.get(coll_path, []):
            prop_parts = prop_path.split(".")
            value = generate_fake_value(full_path, None)
            _set_nested_value(inner_item, prop_parts, value)

        # Check if any nested collections belong inside this one
        for nested_path, _ in collection_paths:
            if nested_path.startswith(coll_path + ".") and nested_path != coll_path:
                if nested_path in built_collections:
                    # Get the property path within this collection
                    suffix = nested_path[len(coll_path) + 1 :]
                    prop_parts = suffix.split(".")
                    # Strip leading numeric indices
                    while prop_parts and prop_parts[0].isdigit():
                        prop_parts.pop(0)
                    if prop_parts:
                        _set_nested_value(
                            inner_item, prop_parts, built_collections[nested_path]
                        )

        # Generate the collection value
        # For .items, check if the dict VALUE is directly iterated as a list
        # e.g., {% for k, v in dict.items %}{% for x in v %}
        # The nested list path would be: coll_path + ".0" with type "list"
        if iteration_type == "items":
            value_is_list = any(
                nested_path == coll_path + ".0" and nested_type == "list"
                for nested_path, nested_type in collection_paths
            )
            # Generate multiple sample entries
            value = {}
            for i in range(1, SAMPLE_ITEMS_COUNT + 1):
                sample_key = _generate_sample_dict_key(coll_path, i)
                if value_is_list:
                    value[sample_key] = [copy.deepcopy(inner_item) if inner_item else {}]
                else:
                    value[sample_key] = copy.deepcopy(inner_item) if inner_item else {}
        else:  # list, values, keys
            # Generate multiple list items
            value = [
                copy.deepcopy(inner_item) if inner_item else {}
                for _ in range(SAMPLE_ITEMS_COUNT)
            ]

        built_collections[coll_path] = value

    # Step 4: Add top-level collections to result
    for coll_path, iteration_type in collection_paths:
        parts = coll_path.split(".")
        # Only add if not nested inside another collection
        is_nested = any(
            coll_path.startswith(other_path + ".") and coll_path != other_path
            for other_path, _ in collection_paths
        )
        if not is_nested:
            _set_nested_value(result, parts, built_collections[coll_path])

    # Step 5: Add remaining scalar paths
    for path, iteration_type in variable_paths.items():
        if iteration_type is None and path not in handled_paths:
            parts = path.split(".")
            if parts[0] in FRAMEWORK_VARS:
                continue
            value = generate_fake_value(path, None)
            _set_nested_value(result, parts, value)

    return result


def _set_nested_value(
    obj: dict | list, parts: list[str], value: str | dict | list
) -> None:
    """
    Recursively set a value in a nested dict/list structure.
    Creates intermediate dicts/lists as needed.
    """
    if len(parts) == 1:
        # Final part - set the value
        final = parts[0]
        if final.isdigit():
            idx = int(final)
            if isinstance(obj, list):
                while len(obj) <= idx:
                    obj.append(value)
                obj[idx] = value
        else:
            if isinstance(obj, dict):
                obj[final] = value
        return

    current_part = parts[0]
    next_part = parts[1]
    is_next_index = next_part.isdigit()

    if current_part.isdigit():
        # Current part is array index
        idx = int(current_part)
        if isinstance(obj, list):
            while len(obj) <= idx:
                obj.append({} if not is_next_index else [])
            _set_nested_value(obj[idx], parts[1:], value)
    else:
        # Current part is object key
        if isinstance(obj, dict):
            if current_part not in obj:
                obj[current_part] = [] if is_next_index else {}
            _set_nested_value(obj[current_part], parts[1:], value)
