import lxml.html
import lxml.etree

from neutron.utils.logging import log_sys_exception


def get_xml_doc_from_html(html):
    # Empty or missing
    if not html:
        return None

    try:
        html = html.encode('utf-8')
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
        log_sys_exception("LXML HTML parse error in `fromstring`")


def get_xpath_from_html(html, xpath_string):
    xml_doc = get_xml_doc_from_html(html)
    if xml_doc is not None and xpath_string:
        return xml_doc.xpath(xpath_string)
