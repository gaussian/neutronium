from neutronium.utils.xpath import (
    get_good_links_from_xml_obj,
    get_xml_obj_from_html,
    get_xpath_from_html,
)


def test_empty_returns_none():
    assert get_xml_obj_from_html("") is None
    assert get_xml_obj_from_html(None) is None


def test_xpath_extracts_text():
    html = "<html><body><p>Hello</p></body></html>"
    assert get_xpath_from_html(html, "//p/text()") == ["Hello"]


def test_good_links_skips_nofollow_keeps_fragments_by_default():
    html = (
        "<html><body>"
        '<a href="http://a.com">A</a>'
        '<a href="#frag">F</a>'
        '<a href="http://b.com" rel="nofollow">B</a>'
        "</body></html>"
    )
    obj = get_xml_obj_from_html(html)
    links = list(get_good_links_from_xml_obj(obj))
    assert "http://a.com" in links
    assert "http://b.com" not in links  # nofollow skipped by default
    assert "#frag" in links  # fragments kept by default (allow_fragments=True)


def test_allow_fragments_false_skips_fragments():
    html = '<html><body><a href="#frag">F</a><a href="http://a.com">A</a></body></html>'
    obj = get_xml_obj_from_html(html)
    links = list(get_good_links_from_xml_obj(obj, allow_fragments=False))
    assert "#frag" not in links
    assert "http://a.com" in links
