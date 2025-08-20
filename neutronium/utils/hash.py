import hashlib


def make_hex_hash_from_str(string: str, digest_size=64) -> str:
    """
    Hashes a very long string using Blake2b.

    Parameters:
        string (str): The input string to hash.

    Returns:
        str: The hexadecimal digest of the hash.
    """

    # Get binary data
    encoded_data = string.encode("utf-8")

    # Hash and return the resulting hexadecimal digest.
    return _make_hash(encoded_data).hexdigest()


def make_bytes_hash_from_bytes(data: bytes, digest_size=64) -> bytes:
    """
    Hashes a byte string using Blake2b.

    Parameters:
        data (bytes): The input byte string to hash.

    Returns:
        bytes: The binary digest of the hash.
    """

    # Hash and return the resulting binary digest.
    return _make_hash(data, digest_size=digest_size).digest()


def _make_hash(data: bytes, digest_size=64):
    """
    Returns a Blake2b hash object for the given binary data.
    """

    # Initialize a Blake2b hash object.
    # We can adjust digest_size if needed.
    hasher = hashlib.blake2b(digest_size=digest_size)

    # If our string is extremely large and you want to minimize memory usage,
    # we could process it in chunks. For an in-memory string, encoding it all
    # at once is acceptable.
    hasher.update(data)

    # Return hasher for either digest or hexdigest
    return hasher
