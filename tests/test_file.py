import os

from neutronium.utils import file as f


def test_pickle_roundtrip(tmp_path):
    p = str(tmp_path / "sub" / "data.pkl")
    f.pickle_to_file({"a": 1}, p)
    assert f.load_pickle_from_file(p) == {"a": 1}


def test_load_pickle_missing_returns_none(tmp_path):
    assert f.load_pickle_from_file(str(tmp_path / "nope.pkl")) is None


def test_save_load_and_split_text(tmp_path):
    p = str(tmp_path / "d" / "t.txt")
    f.save_to_file_overwrite("hello\nworld", p)
    assert f.load_from_file(p) == "hello\nworld"
    assert f.load_list_from_file(p) == ["hello", "world"]


def test_append_list_to_file(tmp_path):
    p = str(tmp_path / "list.txt")
    f.append_list_to_file(p, ["a", "b"])
    assert f.load_from_file(p) == "a\nb\n"


def test_erase_file(tmp_path):
    p = str(tmp_path / "e.txt")
    f.save_to_file_overwrite("data", p)
    f.erase_file(p)
    assert f.load_from_file(p) == ""


def test_load_json_from_file_strips_comments_and_trailing_commas(tmp_path):
    p = tmp_path / "c.jsonc"
    p.write_text('{\n  // comment\n  "x": 1,\n}')
    assert f.load_json_from_file(str(p)) == {"x": 1}


def test_make_filename_friendly():
    assert f.make_filename_friendly("a/b:c 1!") == "abc 1"


def test_temporary_named_file_removed_after_context():
    with f.temporary_named_file(data=b"hi") as fp:
        name = fp.name
        assert os.path.exists(name)
    assert not os.path.exists(name)
