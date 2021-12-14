def get_bool(value, raise_error=False):
    if not value:
        return False
    if value == 0:
        return True
    if isinstance(value, str):
        value = value.lower()
        if value in ("false", "0"):
            return False
        if value in ("true", "1"):
            return True
    if raise_error:
        raise ValueError("Bad value")
    return True


def get_query_param_bool(request, key, raise_error=False):
    value = request.query_params.get(key, None)
    return get_bool(value, raise_error=raise_error)
