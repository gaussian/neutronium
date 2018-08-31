import lxml.html


def get_xml_doc_from_html(html):
    if html:
        try:
            html = html.encode('utf-8')
        except AttributeError:
            pass
        return lxml.html.fromstring(html)


def get_xpath_from_html(html, xpath_string):
    xml_doc = get_xml_doc_from_html(html)
    if xml_doc is not None and xpath_string:
        return xml_doc.xpath(xpath_string)
