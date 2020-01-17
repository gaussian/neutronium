
from urllib.parse import urlparse, parse_qs, urljoin, urlencode
from typing import Tuple, Any, Optional, List, Iterable, Set

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import tldextract

BAD_QUERY_PARAMS = frozenset([
    "gclid", "mkt_tok", "sid", "atrkid", "goal", "_hsenc", "_hsmi", "__hssc", "__hstc", "hsCtaTracking",
    "cx", "ie", "cof", "siteurl", "zanpid", "origin", "refid", "refsrc", "time2", "sa", "ved", "sqi",
    "elqTrackId", "redirect_uri", "redirect_url", "response_type", "_wcsid", "ss", "rt", "epik",
    "cspchd", "elqaid", "_sm_byp", "from", "isappinstalled", "hl", "form", "setlang", "pc", "omwq",
    "inf_contact_key", "pos",
])

BAD_QUERY_PARAM_STARTS = ["mr:", "mc_", "fb", "utm", "facet", "WT."]

GOOD_QUERY_PARAMS = frozenset([
    "id", "ContentId", "page", "p", "output",
])

GOOD_QUERY_PARAM_STARTS = ["date", "ref"]


def strip_query_params(url: str,
                       aggression: int,
                       keep_fragment: bool = True,
                       ) -> Optional[str]:
    """
    Strip query parameters from a URL.
    :param url:
    :param aggression: Between 0 and 2:
        - 0 only removes bad query params.
        - 1 keeps only good query params.
        - 2 removes all query params from a URL.
    :param keep_fragment:
    :return:
    """
    assert 0 <= aggression <= 2

    try:
        url = url.strip()
        o = urlparse(url)
        scheme_prefix = f"{o.scheme}://" if o.scheme else "//"
        # Remove all query params
        url_pre_qs = f"{scheme_prefix}{o.netloc}{o.path}"
        if aggression == 2 or not o.query:
            if keep_fragment:
                return f"{url_pre_qs}#{o.fragment}"
            return url_pre_qs
        # Remove bad query params and rebuild URL
        query_dict = parse_qs(o.query)
        # (some bad querystring)
        if not query_dict and o.query:
            return url
        # Aggression 0: remove only bad query params
        if aggression == 0:
            query_dict = {k: v for k, v in query_dict.items()
                          if k not in BAD_QUERY_PARAMS and
                          not any(k.startswith(bad_start) for bad_start in BAD_QUERY_PARAM_STARTS)}
        # Aggression 1: remove all except good query params
        else:
            query_dict = {k: v for k, v in query_dict.items()
                          if k in GOOD_QUERY_PARAMS or
                          any(k.startswith(good_start) for good_start in GOOD_QUERY_PARAM_STARTS)}
        url = f"{url_pre_qs}?{urlencode(query_dict, doseq=True)}"
        if keep_fragment:
            url = f"{url}#{o.fragment}"
        return url
    except ValueError:
        print(f"Bad URL: {url}")
        return None


def get_url_root(url: str):
    """
    Strip URL down to the scheme/subdomain/domain, e.g. 'https://www.boeing.com'.

    This is often used to get the root URL for later correcting of relative URLs.
    """

    try:
        o = urlparse(url)
        return f"{o.scheme}://{o.netloc}"
    except ValueError:
        print(f"Bad URL: {url}")
        return None


def get_url_domain(url):
    """
    Get domain, e.g. 'boeing.co.uk'.

    This is often used to create a "pretty URL" and also as part of the
    URL normalization process.
    
    Note that this works with emails too, e.g.:
    'john@rex.google.com' => 'google.com'

    """

    subdomain, domain, suffix = tldextract.extract(url)
    if not domain or not suffix:
        return None
    return f"{domain}.{suffix}"


def get_url_path(url):
    try:
        o = urlparse(url, allow_fragments=False)
        return o.path.strip()
    except ValueError:
        print(f"Bad URL: {url}")
        return None


def canonize_url(url: str, root_url=None) -> Optional[str]:
    """
    Put into a canonical (correct) format, removing clearly bad querystrings,
    and correcting relative URLs (if a root URL is provided)

    e.g. '/press?utm_source=123' becomes 'http://hello.com/press'
    """

    # Strip bad querystrings (aggression=0 means only bad ones are stripped)
    url = strip_query_params(url, aggression=0, keep_fragment=True)
    if not url:
        return None

    # Catch the "meow.com" example, where protocol (e.g. http) is missing but
    # the URL is still not relative
    if "//" not in url and get_url_domain(root_url) in url:
        url = "http://" + url

    # Join onto the root (note that the URL's domain will override the root URL's)
    return urljoin(root_url, url)


def normalize_url(url: str) -> Optional[str]:
    """
    Normalize the URL, stripping scheme, www, bad querystrings, extra slashes.

    This should be used for comparing URLs to each other, but is NOT safe to
    use as actual URLs (for this, use `canonize_url()`), because we may damage
    the URL in this process.
    """

    # First strip bad query params (aggression=0 means only bad ones are stripped)
    url = strip_query_params(url, aggression=0)
    if not url:
        return None
    
    # Next, lowercase
    url = url.lower()
    
    # Next, strip the URL starts
    for start in ["http://", "https://", "//", "www."]:
        if url.startswith(start):
            url = url[len(start):]
            
    # Finally, fix the trailing slashes
    url = url.rstrip("/?").replace("/?", "?")

    return url


def get_param_from_url(url, param):
    parsed_url = urlparse(url)
    return parse_qs(parsed_url.query).get(param)


def lower_url(url):
    """
    Get lowercase of all parts of URL
    :param url:
    :return:
    """

    parsed_url = urlparse(url)
    new_url = str(parsed_url.scheme).lower() + "://" + str(parsed_url.netloc).lower() + str(parsed_url.path).lower()
    if parsed_url.params:
        new_url += ";" + str(parsed_url.params)
    if parsed_url.query:
        new_url += "?" + str(parsed_url.query)
    if parsed_url.fragment:
        new_url += "#" + str(parsed_url.fragment)
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
    path = o.path.strip("/")

    # Path and query shouldn't be too long
    if len(path) > 30 or len(o.query) > 30:
        # print(">> " + url)
        return True

    # Shouldn't contain too many hyphens
    num_hyphens = len(path.split("-")) - 1
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


def get_similar_urls(url: str):
    """
    Get the set of URLs which should be considered duplicative of this URL.
    """
    norm_url = normalize_url(url)
    similar_urls = set(h + w + norm_url + e for h in ["http://", "https://", "//", ""]
                       for w in ["www.", ""]
                       for e in ["/", ""])
    similar_urls.add(url)
    return similar_urls


def remove_same_norm_urls(urls: Iterable[str]) -> Set[str]:
    """
    Remove URLs that are HTTP/HTTPS or WWW or "/" duplicates.
    :return:
    """

    # Create a mapping of "normalized" URL to the original URL
    # NOTE: due to the way the dict comprehension works, the LAST VALUE encountered
    #       for a key will be the one kept
    norm_to_url = {normalize_url(u): u for u in urls}

    # The values of this mapping are unique by canonical URL
    return set(norm_to_url.values())


def canonize_and_deduplicate_urls(urls: Iterable[str],
                                  root_url: str = None,
                                  exclude_root: bool = False,
                                  skip_canonization=False,
                                  bad_patterns: Optional[Iterable[str]] = None):
    """
    Fully canonize and deduplicate URLs, including correcting relative URLs.
    """

    # (1) First remove duplicate URLs, according to their "normalized" version
    #     (e.g. URLs that are HTTP/HTTPS or WWW or "/" duplicates)
    urls = remove_same_norm_urls(urls)

    # (2) Remove URLs with bad patterns
    if bad_patterns:
        urls = [u for u in urls if not any(bad in u.lower() for bad in bad_patterns)]

    # (3) Canonize (correct) the URLs, including making relatives absolute
    if not skip_canonization:
        urls = [canonize_url(u, root_url=root_url) for u in urls]

    # (4) Remove root URL, if need be
    if exclude_root:
        urls = [u for u in urls if u != root_url]

    return set(urls)


def link2email(link):
    if "?" not in link:
        link += "?"

    return link + "utm_source"


def extract_dict_from_query_params(query_params, possible_param_definitions: Iterable[Tuple[str, type, Any]]):
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
