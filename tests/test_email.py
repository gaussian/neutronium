from neutronium.utils.email import get_canonical_email


def test_none_and_empty():
    assert get_canonical_email(None) is None
    assert get_canonical_email("") is None


def test_lowercases():
    assert get_canonical_email("Foo@Bar.COM") == "foo@bar.com"


def test_strips_plus_tag():
    assert get_canonical_email("foo+newsletter@bar.com") == "foo@bar.com"


def test_collapses_extra_at_signs():
    assert get_canonical_email("a@b@bar.com") == "ab@bar.com"
