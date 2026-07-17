from neutronium.utils import url


def test_is_url_valid_stayed_in_neutron():
    # is_url_valid uses Django's URLValidator and must NOT be in neutronium.
    assert not hasattr(url, "is_url_valid")


def test_parse_url_empty_returns_none():
    assert url.parse_url("") is None


def test_parse_url_lowercases_netloc_and_strips_default_port():
    o = url.parse_url("http://Example.COM:80/Path")
    assert o.scheme == "http"
    assert o.netloc == "example.com"
    assert o.path == "/Path"


def test_get_url_root_canonized():
    assert url.get_url_root_canonized("http://www.example.com/a/b?q=1") == "http://www.example.com"


def test_get_url_path_strips_slashes():
    assert url.get_url_path("http://example.com/a/b/") == "a/b"


def test_get_url_domain_basic():
    assert url.get_url_domain("http://www.boeing.co.uk/jobs") == "boeing.co.uk"


def test_get_url_domain_with_subdomain():
    assert url.get_url_domain("http://www.boeing.co.uk", include_subdomain=True) == "www.boeing.co.uk"
