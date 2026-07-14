def get_xml_obj_from_html(html):
    import lxml.html
    import lxml.etree

    # Empty or missing
    if not html:
        return None

    try:
        html = html.encode("utf-8")
    except AttributeError:
        pass

    # Empty or missing
    if not html or html.isspace():
        return None

    # Get XML
    try:
        return lxml.html.fromstring(html)

    # Parser error, likely no-text HTML (i.e. whole thing is comments or tags)
    except lxml.etree.ParserError as e:
        if str(e) == "Document is empty":
            return None
        raise


def get_xpath_from_html(html, xpath_string):
    xml_obj = get_xml_obj_from_html(html)
    if xml_obj is not None and xpath_string:
        return xml_obj.xpath(xpath_string)


def get_good_links_from_xml_obj(xml_obj, titles=False, allow_fragments=True, skip_nofollow=True):
    def url_ok(u):
        return u and (allow_fragments or u[0] != "#")

    if skip_nofollow:
        link_xpath = "//a[not(@rel='nofollow')]"
    else:
        link_xpath = "//a"
    link_url_xpath = f"{link_xpath}/@href"

    if titles:
        return ((e.get("href").strip(), e.text.strip() if e.text else e.text)
                for e in xml_obj.xpath(link_xpath)
                if url_ok(e.get("href")))

    return (h.strip()
            for h in xml_obj.xpath(link_url_xpath)
            if url_ok(h))
