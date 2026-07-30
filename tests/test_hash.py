import hashlib

from neutronium.utils.hash import make_bytes_hash_from_bytes, make_hex_hash_from_str


def test_bytes_hash_matches_blake2b():
    data = b"test content for hashing"
    expected = hashlib.blake2b(data, digest_size=64).digest()
    assert make_bytes_hash_from_bytes(data) == expected


def test_bytes_hash_length_and_determinism():
    result = make_bytes_hash_from_bytes(b"abc")
    assert isinstance(result, bytes)
    assert len(result) == 64
    assert result == make_bytes_hash_from_bytes(b"abc")
    assert result != make_bytes_hash_from_bytes(b"abd")


def test_bytes_hash_empty_input():
    expected = hashlib.blake2b(b"", digest_size=64).digest()
    assert make_bytes_hash_from_bytes(b"") == expected


def test_hex_hash_matches_blake2b():
    s = "hello wörld"  # non-ascii to pin utf-8 encoding
    expected = hashlib.blake2b(s.encode("utf-8"), digest_size=64).hexdigest()
    assert make_hex_hash_from_str(s) == expected


def test_hex_hash_shape_and_consistency_with_bytes_variant():
    s = "consistency check"
    hex_result = make_hex_hash_from_str(s)
    assert isinstance(hex_result, str)
    assert len(hex_result) == 128  # 64 bytes -> 128 hex chars
    assert hex_result == make_bytes_hash_from_bytes(s.encode("utf-8")).hex()
