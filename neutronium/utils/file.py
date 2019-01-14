import os
import tempfile
import pickle
from contextlib import contextmanager

from django.core import serializers


def load_pickle_from_file(file_path: str):
    # Open and load if file exists
    if os.path.exists(file_path):
        with open(file_path, 'rb') as handle:
            return pickle.load(handle)

    # File doesn't exist
    return None


def pickle_to_file(obj, file_path: str):
    # Make directory if needed
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Pickle
    with open(file_path, 'wb') as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_pickle_from_file_or_function(file_path: str, obj_create_func):
    # Try to load pickle
    obj = load_pickle_from_file(file_path)

    # File doesn't exist
    if not obj:

        # Create the object
        obj = obj_create_func()

        # Pickle the object
        pickle_to_file(obj, file_path)

    return obj


def load_from_file(file_path: str, encoding=None, binary=False):
    if os.path.exists(file_path):
        mode = 'rb' if binary else 'r'
        with open(file_path, mode=mode, encoding=encoding) as handle:
            return handle.read()
    return None


def save_to_file_overwrite(text, file_path: str):
    # Make directory if needed
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Open
    with open(file_path, 'w') as handle:
        handle.write(text)


def load_list_from_file(file_path, encoding=None):
    file_contents = load_from_file(file_path, encoding=encoding)
    if file_contents:
        return file_contents.split('\n')
    return None


def append_list_to_file(file_path, items):
    with open(file_path, 'ab+') as handle:
        for item in items:
            handle.write((item + '\n').encode('utf-8'))


def erase_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'w+') as handle:
            handle.write('')


def serialize_to_file(querysets, file_path):
    with open(file_path, "w+") as out:
        for queryset in querysets:
            serializers.serialize('json', queryset, stream=out)


@contextmanager
def temporary_named_file(data, binary=True, encoding=None):
    """Windows-friendly temp named file context manager."""
    mode = 'w+b' if binary else 'w+'
    fp = tempfile.NamedTemporaryFile(delete=False, encoding=encoding, mode=mode)
    fp.write(data)
    fp.close()
    yield fp
    os.remove(fp.name)
