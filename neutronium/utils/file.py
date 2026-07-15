import os
import tempfile
import pickle
from contextlib import contextmanager


def load_pickle_from_file(file_path: str):
    # Open and load if file exists
    if os.path.exists(file_path):
        with open(file_path, "rb") as handle:
            try:
                return pickle.load(handle)
            except EOFError:
                pass

    # File doesn't exist or is empty/poorly formatted
    return None


def pickle_to_file(obj, file_path: str):
    # Make directory if needed
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Erase the file
    erase_file(file_path)

    # Pickle
    with open(file_path, "wb") as handle:
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
        mode = "rb" if binary else "r"
        with open(file_path, mode=mode, encoding=encoding) as handle:
            return handle.read()
    return None


def save_to_file_overwrite(text, file_path: str):
    # Make directory if needed
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Open
    with open(file_path, "w") as handle:
        handle.write(text)


def load_list_from_file(file_path: str, encoding=None):
    file_contents = load_from_file(file_path, encoding=encoding)
    if file_contents:
        return file_contents.split("\n")
    return None


def append_list_to_file(file_path: str, items):
    with open(file_path, "ab+") as handle:
        for item in items:
            handle.write((item + "\n").encode("utf-8"))


def load_json_from_file(file_path: str, encoding=None) -> dict | list | None:
    """
    Load a JSONC file (JSON with comments) and return the parsed object.

    Args:
        filename: Path to the JSONC file, relative to the fixtures/test_data directory

    Returns:
        dict | list | None: The parsed JSON object
    """
    import json
    import re

    # Read the file
    file_contents = load_from_file(file_path, encoding=encoding)
    if not file_contents:
        return None

    # Remove comments (both single-line and multi-line)
    file_contents = re.sub(r"//.*?\n", "\n", file_contents)  # Remove single-line comments
    file_contents = re.sub(
        r"/\*.*?\*/", "", file_contents, flags=re.DOTALL
    )  # Remove multi-line comments

    # Remove trailing commas (not valid in JSON but common in JSONC)
    file_contents = re.sub(r",\s*([\]\}])", r"\1", file_contents)

    # Parse and return the JSON
    return json.loads(file_contents)


def erase_file(file_path: str):
    if os.path.exists(file_path):
        with open(file_path, "w+") as handle:
            handle.write("")


JSON_DATE_SERIALIZE_FORMAT = "%Y-%m-%d %H:%M:%S"


def json_serialize(obj):
    import json
    import datetime

    class Encoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, str):
                return o
            if isinstance(o, set):
                return [self.default(oi) for oi in o]
            if isinstance(o, datetime.datetime):
                return o.strftime(JSON_DATE_SERIALIZE_FORMAT)
            if (
                isinstance(o, tuple)
                and hasattr(o, "_fields")
                and "__repr__" in o.__class__.__dict__
            ):
                return o.__repr__()
            return json.JSONEncoder.default(self, o)

    return json.dumps(obj, cls=Encoder, indent=4)


def make_filename_friendly(filename: str) -> str:
    return "".join(
        [c for c in filename if c.isalpha() or c.isdigit() or c == " "]
    ).rstrip()


@contextmanager
def temporary_named_file(data=None, binary=True, encoding=None, suffix=None):
    """Windows-friendly temp named file context manager."""
    mode = "w+b" if binary else "w+"
    fp = tempfile.NamedTemporaryFile(
        delete=False, encoding=encoding, mode=mode, suffix=suffix
    )
    if data is not None:
        fp.write(data)
    yield fp
    fp.close()
    os.remove(fp.name)
