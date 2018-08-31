"""
(c) 2017 Gaussian Holdings, LLC
"""
import types


def batch(iterable, batch_size):
    assert isinstance(iterable, list)

    num_items = len(iterable)
    for ndx in range(0, num_items, batch_size):
        yield iterable[ndx:min(ndx + batch_size, num_items)]


def batch_from_generator(gen_obj, batch_size):
    assert isinstance(gen_obj, types.GeneratorType)

    while True:
        generated_batch = []

        # Build and yield an array of generated items
        try:
            for i in range(0, batch_size):
                generated_batch.append(next(gen_obj))
            yield generated_batch

        # Yield what remains
        except StopIteration:
            yield generated_batch
            return


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


def multi_needle_search(haystack, needles):
    for needle in needles:
        if needle in haystack:
            return True
    return False


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
