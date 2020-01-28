
import types

from typing import Collection, Iterable, List


def batch(iterable: Iterable, batch_size):
    if isinstance(iterable, list) or isinstance(iterable, str):
        num_items = len(iterable)
        for ndx in range(0, num_items, batch_size):
            yield iterable[ndx:min(ndx + batch_size, num_items)]
    elif isinstance(iterable, types.GeneratorType):
        while True:
            generated_batch = []

            # Build and yield an array of generated items
            try:
                for i in range(0, batch_size):
                    generated_batch.append(next(iterable))
                yield generated_batch

            # Yield what remains
            except StopIteration:
                yield generated_batch
                return
    else:
        raise ValueError(f"Bad iterable type: {type(iterable)}, try `list` or `generator`")


def separate(iterables: Iterable, condition: types.FunctionType) -> (List, List):
    """Split one iterable into 2 lists, based on whether a condition is met"""
    good, bad = [], []
    for it in iterables:
        good.append(it) if condition(it) else bad.append(it)
    return good, bad


def dedup_objs_by_id(objs):
    output_objs = []
    output_ids = []
    for obj in objs:
        if obj.id not in output_ids:
            output_ids.append(obj.id)
            output_objs.append(obj)
    return output_objs


def dedup_objs_by_attr(objs, key):
    output_objs = []
    output_values = set()
    for obj in objs:
        value = getattr(obj, key)
        if value not in output_values:
            output_values.add(value)
            output_objs.append(obj)
    return output_objs


def remove_obj_from_array_by_id(objs, id_to_remove):
    output_objs = []
    for obj in objs:
        if obj.id != id_to_remove:
            output_objs.append(obj)
    return output_objs


def remove_objs_from_set(master_set, removal_objs):
    for item in removal_objs:
        try:
            master_set.remove(item)
        except KeyError:
            pass
    return master_set


# TODO: deprecated, delete this
def multi_needle_search(haystack: Collection, needles: Collection):
    for needle in needles:
        if needle in haystack:
            return True
    return False


def many(iterable, n):
    """
    This function returns whether the iterable is True at least n times.

    It is similar to `any`, where `any` returns whether the iterable is
    True at least 1 time.

    Source: https://stackoverflow.com/a/42514511
    """
    iterable = iter(iterable)
    return all(any(iterable) for _ in range(n))


def get_obj_properties_dict_from_config(obj, config_tuples):
    output = dict()
    for config_tuple in config_tuples:
        key_field_name = config_tuple[0]
        obj_field_name = config_tuple[1]
        obj_attribute = getattr(obj, obj_field_name, "")
        obj_attribute = "" if obj_attribute is None else obj_attribute
        if not isinstance(obj_attribute, (str, int, float)):
            obj_attribute = str(obj_attribute)
        output[key_field_name] = obj_attribute
    return output


def get_dict_from_tuple(input_tuple):
    output_dict = dict()
    for item in input_tuple:
        output_dict[str(item[0])] = item[1]
    return output_dict


def intersection(lst1, lst2):
    # Source: https://www.geeksforgeeks.org/python-intersection-two-lists/
    temp = set(lst2)
    return [value for value in lst1 if value in temp]


def is_in_sequence(list_inner: list, list_outer: list):
    # No way a longer list can be contained by shorter
    if len(list_inner) > len(list_outer):
        return False

    # Iterate through parent list (i) and inner list (j)
    i, j = 0, 0
    while i < len(list_outer):

        # Check if values are the same - if so, advance i and j
        if list_outer[i] == list_inner[j]:
            i += 1
            j += 1

            # Matched all of inner list - we're done
            if j == len(list_inner):
                return True
            continue

        # Failed to match - reset j to search from start of inner list, and retreat by 1 on outer loop
        elif j > 0:
            j = 0
        else:
            i += 1

    # No match found
    return False
