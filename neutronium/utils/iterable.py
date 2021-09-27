
import types
from itertools import chain, starmap, islice

from typing import Collection, Iterable, List, Any, Tuple, Dict


def batch(iterable: Iterable, batch_size):
    """
    Batching of any arbitrary iterable, including generators
    Source: https://code.activestate.com/recipes/303279-getting-items-in-batches/
    """
    sourceiter = iter(iterable)
    try:
        while True:
            batchiter = islice(sourceiter, batch_size)
            yield chain([next(batchiter)], batchiter)
    except StopIteration:
        return


def precomputed_batch(iterable: Iterable, batch_size):
    """
    Batches you can use len() on
    """
    if isinstance(iterable, list) or isinstance(iterable, str):
        num_items = len(iterable)
        for ndx in range(0, num_items, batch_size):
            yield iterable[ndx:min(ndx + batch_size, num_items)]
    else:
        raise ValueError(f"Bad iterable type: {type(iterable)}, try `list` or `str`")


def separate(iterables: Iterable, condition: types.FunctionType) -> (List, List):
    """Split one iterable into 2 lists, based on whether a condition is met"""
    good, bad = [], []
    for it in iterables:
        good.append(it) if condition(it) else bad.append(it)
    return good, bad


def dedup(items: Iterable) -> List:
    output_set, output_list = set(), []
    for item in items:
        if item not in output_set:
            output_list.append(item)
            output_set.add(item)
    return output_list


def dedup_objs_by_attr(objs: Iterable, key: str) -> (List, List):
    output_objs, removed_objs = [], []
    output_values = set()
    for obj in objs:
        value = getattr(obj, key)
        if value not in output_values:
            output_values.add(value)
            output_objs.append(obj)
        else:
            removed_objs.append(obj)
    return output_objs, removed_objs


def dedup_objs_by_id(objs: Iterable) -> (List, List):
    return dedup_objs_by_attr(objs, "id")


def remove_obj_from_array_by_id(objs: Iterable, id_to_remove):
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


def flatten_dict(dictionary, value_op=None) -> Dict[Tuple, Any]:
    """
    Flatten a nested dictionary structure. Return format is {(a, b, c, d...): value}

    Based on https://codereview.stackexchange.com/a/173483
    """

    def unpack(parent_key, parent_value):
        """Unpack one level of nesting in a dictionary"""
        try:
            items = parent_value.items()
        except AttributeError:
            # parent_value was not a dict, no need to flatten
            yield (parent_key, parent_value)
        else:
            for key, value in items:
                if value_op:
                    value = value_op(key, value)
                yield parent_key + (key,), value

    # Put each key into a tuple to initiate building a tuple of subkeys
    dictionary = {(key,): value for key, value in dictionary.items()}

    while True:
        # Keep unpacking the dictionary until all value's are not dictionary's
        dictionary = dict(chain.from_iterable(starmap(unpack, dictionary.items())))
        if not any(isinstance(value, dict) for value in dictionary.values()):
            break

    return dictionary


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


def str_split_multi(text: str, substrings: Iterable[str]):
    if not text:
        return []
    text_chunks = [text]
    for substring in substrings:
        text_chunks = chain(*[chunk.split(substring) for chunk in text_chunks])
    return text_chunks
