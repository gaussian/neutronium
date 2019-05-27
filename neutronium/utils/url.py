from urllib.parse import urlparse, parse_qs, urljoin

from django.conf import settings
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from typing import Tuple, Any, Sequence


def strip_querystring_from_url(url):
    try:
        o = urlparse(url)
        return f'{o.scheme}://{o.netloc}{o.path}'
    except ValueError:
        print("Bad URL: " + url)
        return None


def get_url_root(url):
    try:
        o = urlparse(url)
        return f'{o.scheme}://{o.netloc}'
    except ValueError:
        print("Bad URL: " + url)
        return None


def get_url_domain(url):
    try:
        if "//" not in url:
            url = f"http://{url}"
        return f'{urlparse(url).netloc}'
    except ValueError:
        print(f"Bad URL: {url}")
        return None


def get_url_path(url):
    try:
        o = urlparse(url, allow_fragments=False)
        return o.path
    except ValueError:
        print(f"Bad URL: {url}")
        return None


def strip_url_protocol(url):
    # NOTE: order matters
    for start in ["http://", "https://", "//", "www."]:
        if url.startswith(start):
            url = url[len(start):]
    url = url.rstrip('/')
    return url


def pretty_url(url):
    o = urlparse(url)
    new_url = str(o.netloc).replace("www.", "")
    url_split_by_periods = new_url.split('.')
    if len(url_split_by_periods) > 2 and url_split_by_periods[-1] in ['com', 'edu', 'org']:
        new_url = '.'.join(url_split_by_periods[1:])
    return new_url


def get_param_from_url(url, param):
    parsed_url = urlparse(url)
    return parse_qs(parsed_url.query).get(param)


def lower_url(url):
    """
    Get lowercase of all parts of URL except querystring
    :param url:
    :return:
    """
    parsed_url = urlparse(url)
    new_url = str(parsed_url.scheme).lower() + "://" + str(parsed_url.netloc).lower() + str(parsed_url.path).lower()
    if parsed_url.params:
        new_url += ';' + str(parsed_url.params)
    if parsed_url.query:
        new_url += '?' + str(parsed_url.query)
    if parsed_url.fragment:
        new_url += '#' + str(parsed_url.fragment)
    return new_url


def is_url_valid(url):
    if not url:
        return False
    validator = URLValidator()
    try:
        validator(url)
        return True
    except ValidationError:
        return False


def could_url_be_article(url):
    o = urlparse(url)
    path = o.path.strip('/')

    # Path and query shouldn't be too long
    if len(path) > 30 or len(o.query) > 30:
        # print(">> " + url)
        return True

    # Shouldn't contain too many hyphens
    num_hyphens = len(path.split('-')) - 1
    if num_hyphens > 3:
        # print(">> " + url)
        return True

    # Shouldn't end in a number
    if path[-1:].isdigit():
        return True

    return False


def get_stripped_urls(urls, strip_down_to_substring):
    """
    Get the result of stripping each URL down to the provided substring.

    e.g. ['http://hello.com/rss/meow'] becomes ['http://hello.com/rss'] if substring is '/rss'

    :param urls:
    :param strip_down_to_substring:
    :return:
    """
    stripped_urls = []
    for url in urls:
        split_url = url.split(strip_down_to_substring)
        if len(split_url) > 1:
            stripped_urls.append(split_url[0] + strip_down_to_substring)
    return stripped_urls


def correct_relative_url(url: str, root_url: str) -> str:
    """
    Put into a canonical format, e.g. '/press' becomes 'http://hello.com/press'

    :param url:
    :type url: string
    :param root_url:
    :type root_url: string
    :return:
    """

    # Protocol included - can return immediately
    if any(url.startswith(f) for f in ("https", "http", "//")):
        return url

    # Catch the "meow.com" example, where protocol (e.g. http) is missing
    if strip_url_protocol(root_url) in url and '//' not in url:
        url = 'http://' + url

    # Join onto the root
    return urljoin(root_url, url)


def get_similar_urls(url: str):
    """
    Get the set of URLs which should be considered duplicative of this URL.
    """
    stripped_url = strip_url_protocol(url)
    return set(h + w + b + e for h in ["http://", "https://", "//", ""]
               for w in ["www.", ""]
               for b in [stripped_url, stripped_url.lower()]
               for e in ["/", ""])


def remove_duplicate_urls(urls: Sequence[str]):
    """
    Remove URLs that are HTTP/HTTPS or WWW or "/" duplicates.
    :return:
    """

    # Strip URLs
    urls = [u.strip() for u in urls]

    # Create a mapping of "lowercase stripped" URL to the original URL
    # NOTE: due to the way the dict comprehension works, the LAST VALUE encountered
    #       for a key will be the one kept
    urls_by_canonical = {strip_url_protocol(u).lower(): u for u in urls}

    # The values of this mapping are unique by canonical URL
    return urls_by_canonical.values()


def correct_and_deduplicate_urls(urls, base_url):
    """

    :param urls:
    :type urls: set
    :param base_url:
    :return:
    """

    # Correct the URLs
    if base_url:
        urls = set(correct_relative_url(u, base_url) for u in urls)

    # Remove URLs that are HTTP/HTTPS or WWW or "/" duplicates
    urls = remove_duplicate_urls(urls)

    # Remove base URL, if it pops up
    urls = [u for u in urls if u != base_url]

    # Remove feeds with bad patterns
    filtered_feed_urls = set()
    bad_patterns = settings.BAD_FEED_URL_PATTERNS
    for url in urls:
        u = url.lower()
        found_bad_pattern = False
        for bad_pattern in bad_patterns:
            if bad_pattern in u:
                found_bad_pattern = True
                break
        if not found_bad_pattern:
            filtered_feed_urls.add(url)

    return filtered_feed_urls


def link2email(link):
    if '?' not in link:
        link += '?'

    return link + "utm_source"


def extract_dict_from_query_params(query_params, possible_param_definitions: Sequence[Tuple[str, type, Any]]):
    """
    Extracts and converts QueryDict into a correctly typed dict.

    Expects possible_param_definitions to be a list of tuples of (param_name, param_type, param_default),
    e.g.
    [
        ('page', int),
        ('search_terms', list),
    ]

    :param query_params:
    :type query_params: django.http.QueryDict
    :param possible_param_definitions:
    :return:
    """

    def get_param_from_def(param_name, param_type, param_default):
        if param_type == list:
            param = query_params.getlist(param_name, None)
        else:
            param = query_params.get(param_name, None)
        if param:
            if param_type == int:
                param = int(param)
            elif param_type == bool:
                param = param.lower() == "true"
        else:
            param = param_default
        return param

    return {pn: get_param_from_def(pn, pt, pd)
            for pn, pt, pd in possible_param_definitions}
