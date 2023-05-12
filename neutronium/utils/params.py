from typing import Tuple, Iterable, Union


def get_bool(value, raise_error=False):
    if not value:
        return False
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


def build_dict_from_request_params(request, config_tuples: Iterable[Tuple[str, Union[type, dict]]]):
    output_dict = dict()

    for dict_key, config_or_key_type in config_tuples:
        if isinstance(config_or_key_type, type):
            param_keys_to_try = [dict_key]
            key_type = config_or_key_type
        else:
            param_keys_to_try = config_or_key_type.get("param_keys_to_try", [dict_key])
            try:
                key_type = config_or_key_type["key_type"]
            except KeyError:
                raise ValueError("2nd item in config tuple needs to be a `type` or have key called `key_type`")

        # Multiple param_keys, meaning that different query params can be tried
        # until one is found
        for param_key in param_keys_to_try:

            # Once the dict_key has been set once, continue
            if dict_key in output_dict:
                break

            # Get the value from the query params, and set to the dict
            set_param_value_to_dict(
                request=request,
                param_key=param_key,
                key_type=key_type,
                dict_key=dict_key,
                output_dict=output_dict
            )

    return output_dict


def set_param_value_to_dict(request, param_key: str, key_type: type, dict_key: str, output_dict: dict):
    if param_key not in request.query_params:
        return

    # NOTE: no default values are given for get/getlist because existence of
    #       key should already have been checked
    if key_type == bool:
        output_dict[dict_key] = get_query_param_bool(request, param_key)
    elif key_type == list:
        output_dict[dict_key] = request.query_params.getlist(param_key)
    elif key_type == str:
        output_dict[dict_key] = request.query_params.get(param_key)
    elif key_type == int:
        output_dict[dict_key] = int(request.query_params.get(param_key))
