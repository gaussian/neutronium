
from urllib.parse import urlparse, parse_qs, urljoin, urlencode, ParseResult
from typing import Tuple, Any, Optional, List, Iterable, Set

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

BAD_QUERY_PARAMS = frozenset([
    "gclid", "mkt_tok", "sid", "atrkid", "goal", "_hsenc", "_hsmi", "__hssc", "__hstc", "hsCtaTracking",
    "cx", "ie", "cof", "siteurl", "zanpid", "origin", "refid", "refsrc", "time2", "sa", "ved", "sqi",
    "elqTrackId", "redirect_uri", "redirect_url", "response_type", "_wcsid", "ss", "rt", "epik",
    "cspchd", "elqaid", "_sm_byp", "from", "isappinstalled", "hl", "form", "setlang", "pc", "omwq",
    "inf_contact_key", "pos", "feedref",
])

BAD_QUERY_PARAM_STARTS = ("mr:", "mc_", "fb", "utm", "facet", "WT.")

BAD_QUERY_PARAM_ENDS = ("campaign", "source", "medium", "_term")

GOOD_QUERY_PARAMS = frozenset([
    "id", "ContentId", "page", "p", "output",
])

GOOD_QUERY_PARAM_STARTS = ["date", "ref"]

USE_CACHE = True
CACHE_SIZE = 1000

normalized_url_cache = dict()
canonized_url_cache = dict()


def parse_url(url: str, correct_root: bool = True, **kwargs) -> Optional[ParseResult]:
    """
    Correct the URL then parse it (as urlparse is bad at handling relative URLs)
    """

    # (0) Support function for correcting and adding scheme
    # NOTE: it is critical this happens BEFORE parse_url!
    def prepend_protocol(u, prefix=""):
        # HTTPS protocol...
        if ":443" in u:
            # Make sure ":443" occurs before the path, by checking number of slashes
            # (number of slashes before the ":443" should be 2, remember to factor in the prefix)
            if u.split(":443")[0].count("/") + prefix.count("/") == 2:
                return f"https:{prefix}{u}".replace(":443", "")
        # ...otherwise HTTP
        return f"http:{prefix}{u}"

    # (1) PREPARE URL
    if not url:
        return None
    # Strip
    url = url.strip()
    # Make sure URL has a protocol (unless it doesn't appear to have a domain, in
    # which case this is probably a relative URL
    if url.startswith("//"):
        # e.g. "//boeing.com"
        url = prepend_protocol(url)
    elif "//" not in url[:10]:
        # Domain exists, e.g. "boeing.com"
        if get_url_domain(url):
            url = prepend_protocol(url, "//")
        # Otherwise, no domain in the URL - must be a relative link, e.g. "/contact-us"
        else:
            pass

    # (2) PARSE
    try:
        url_obj = urlparse(url, **kwargs)
    except ValueError:
        print(f"Bad URL: {url}")
        return None

    # (3) POST-PROCESS
    if correct_root:
        # Remove redundant ports
        netloc = url_obj.netloc
        if ((":80/" in netloc or netloc.endswith(":80")) and url_obj.scheme == "http") or \
                ((":443/" in netloc or netloc.endswith(":443")) and url_obj.scheme == "https"):
            netloc = netloc.partition(":")[0]
        # Lowercase
        netloc = netloc.lower()
        # Update
        url_obj = url_obj._replace(netloc=netloc)

    return url_obj


def rebuild_url(url: str,
                url_obj: ParseResult = None,
                aggression: int = 0,
                ) -> Optional[str]:
    """
    Rebuild a URL correctly, stripping query parameters if needed, and lowercasing the
    scheme and hostname.
    :param url: Original URL
    :param url_obj: Pre-parsed URL object
    :param aggression: How aggressively to remove querystring params/fragments? Between 0 and 3:
        - 0 no removal.
        - 1 only removes bad query params.
        - 2 keeps only good query params, AND removes fragments.
        - 3 removes all query params from a URL, AND removes fragments.
    :return: new URL
    """
    assert 0 <= aggression <= 3

    # (1) PREPARE
    # Parse URL or use existing parsed object
    o = url_obj or parse_url(url)
    if not o or not url:
        return None
    # Try to build the scheme/domain
    if o.scheme and o.netloc:
        scheme_prefix = f"{o.scheme}://"
    else:
        scheme_prefix = ""
    url_root = f"{scheme_prefix}{o.netloc}"
    # Add the URL path
    url_pre_qs = f"{url_root}{o.path}"
    # Pre-calculate fragment string - only add fragment if:
    # (a) aggression is low enough
    # (b) a fragment exists
    if aggression >= 2 or not o.fragment:
        fragment_suffix = ""
    else:
        fragment_suffix = f"#{o.fragment}"

    # (2) HANDLE WITHOUT REBUILDING QUERYSTRING
    # == Aggression 3: remove whole querystring
    if aggression == 3:
        return url_pre_qs
    # No querystring, exit early
    if not o.query:
        return f"{url_pre_qs}{fragment_suffix}"
    # == Aggression 0: no querystring removal (and based on the above, we know we have a querystring)
    if aggression == 0:
        return f"{url_pre_qs}?{o.query}{fragment_suffix}"

    # (3) STRIP AND REBUILD QUERYSTRING
    query_dict = parse_qs(o.query, keep_blank_values=True)
    # Bad querystring (o.query is definitely not null), so return original URL
    if not query_dict:
        return url.rstrip("/")
    # == Aggression 1: remove only bad query params
    if aggression == 1:
        query_dict = {k: v for k, v in query_dict.items()
                      if k not in BAD_QUERY_PARAMS and
                      not any(k.startswith(bad_start) for bad_start in BAD_QUERY_PARAM_STARTS) and
                      not any(k.endswith(bad_end) for bad_end in BAD_QUERY_PARAM_ENDS)}
    # == Aggression 2: remove all except good query params
    else:
        query_dict = {k: v for k, v in query_dict.items()
                      if k in GOOD_QUERY_PARAMS or
                      any(k.startswith(good_start) for good_start in GOOD_QUERY_PARAM_STARTS)}
    if query_dict:
        querystring = f"?{urlencode(query_dict, doseq=True)}"
    else:
        querystring = ""
    return f"{url_pre_qs}{querystring}{fragment_suffix}"


def get_url_root_canonized(url: str) -> Optional[str]:
    """
    Strip URL down to the scheme/subdomain/domain, e.g. 'https://www.boeing.com'.
    This is often used to get the root URL for later correcting of relative URLs.
    This function CANNOT handle relative URLs.
    """

    # Parse and handle
    o = parse_url(url)
    if not o:
        return None

    return f"{o.scheme}://{o.netloc}"


def get_url_domain(url, include_subdomain=False) -> Optional[str]:
    """
    Get domain, e.g. 'boeing.co.uk'.

    This is often used to create a "pretty URL" and also as part of the
    URL normalization process.

    Note that this works with emails too, e.g.:
    'john@rex.google.com' => 'google.com'
    """

    import tldextract

    if not url:
        return None

    # Extract
    ext = tldextract.extract(url)
    subdomain, domain, suffix = ext.subdomain, ext.domain, ext.suffix
    if not domain:
        return None

    # No suffix, is it likely IP address?
    if not suffix:
        if domain.count(".") < 3:
            # Special case for docker internal
            if domain.lower() == "internal":
                return f"{subdomain.lower()}.{domain.lower()}"
            return None
        return domain

    # Expected configuration
    output = f"{domain.lower()}.{suffix.lower()}"
    if include_subdomain and subdomain:
        return f"{subdomain.lower()}.{output}"
    return output


def get_url_path(url: str) -> Optional[str]:
    o = parse_url(url, correct_root=True)
    if not o:
        return None
    # Strip spaces and slashes
    return o.path.strip("/ ")


def canonize_url(url: str, root_url=None) -> Optional[str]:
    """
    Put into a canonical (correct) format, removing clearly bad querystrings,
    and correcting relative URLs (if a root URL is provided)

    e.g. '/press?utm_source=123' becomes 'http://hello.com/press'
    """

    # Get from cache if possible
    global canonized_url_cache
    cache_key = f"{url}||{root_url}"
    if USE_CACHE:
        cache_value = canonized_url_cache.get(cache_key, None)
        if cache_value:
            return cache_value

    # Strip bad querystrings (aggression=1 means only bad ones are stripped)
    url_obj = parse_url(url)
    if not url_obj:
        return None
    url = rebuild_url(url, url_obj, aggression=1)
    if not url:
        return None

    # Join onto the root (note that the URL's domain will override the root URL's)
    url = urljoin(root_url, url)

    # Store in cache if possible, OR wipe the cache if too many URLs
    if USE_CACHE:
        if len(canonized_url_cache) > CACHE_SIZE:
            canonized_url_cache = dict()
        else:
            canonized_url_cache[cache_key] = url

    return url


def normalize_url(url: str) -> Optional[str]:
    """
    Normalize the URL, stripping scheme, www, bad querystrings, extra slashes.

    This should be used for comparing URLs to each other, but is NOT safe to
    use as downloadable URLs (for this, use `canonize_url()`), because we may
    damage the URL in this process.
    """

    # Get from cache if possible
    global normalized_url_cache
    cache_key = url
    if USE_CACHE:
        cache_value = normalized_url_cache.get(cache_key, None)
        if cache_value:
            return cache_value

    # First strip bad query params (aggression=1 means only bad ones are stripped)
    url_obj = parse_url(url)
    if not url_obj:
        return None
    url = rebuild_url(url, url_obj, aggression=1)
    if not url:
        return None

    # Next, lowercase
    url = url.lower()

    # Next, remove ports (e.g. //boeing.com:443)
    if ":" in url_obj.netloc:
        old_netloc = url_obj.netloc.lower()
        new_netloc = old_netloc.partition(":")[0]
        url = url.replace(old_netloc, new_netloc)

    # Next, strip the URL starts
    url = url.partition("://")[-1] or url
    for start in ["//", "www.", "m."]:
        if url.startswith(start):
            url = url[len(start):]

    # Finally, fix the trailing slashes
    url = url.rstrip("/?").replace("/?", "?")

    # Store in cache if possible, OR wipe the cache if too many URLs
    if USE_CACHE:
        if len(normalized_url_cache) > CACHE_SIZE:
            normalized_url_cache = dict()
        else:
            normalized_url_cache[cache_key] = url

    return url


def get_param_from_url(url, param) -> Optional[str]:
    url_obj = parse_url(url)
    if not url_obj:
        return None
    return parse_qs(url_obj.query).get(param)


def is_url_valid(url: str) -> bool:
    if not url:
        return False
    validator = URLValidator()
    try:
        validator(url)
        return True
    except ValidationError:
        return False


def get_stripped_urls(urls: Iterable[str], strip_down_to_substring: str):
    """
    Get the result of stripping each URL down to the provided substring.

    e.g. ['http://hello.com/rss/meow'] becomes ['http://hello.com/rss'] if substring is '/rss'

    :param urls:
    :param strip_down_to_substring:
    :return:
    """
    # Remember that partition() gives a tuple length 3
    return ["".join(u.partition(strip_down_to_substring)[:2])
            for u in urls]


def get_similar_urls(url: str) -> Optional[Set[str]]:
    """
    Get the set of URLs which should be considered duplicative of this URL.
    """
    normalized_url = normalize_url(url)
    if not normalized_url:
        return set()

    # Allow trailing "/" if URL doesn't have querystring/fragment
    if "?" in normalized_url or "#" in normalized_url:
        endings = [""]
    else:
        endings = ["/", ""]

    similar_urls = set(h + w + normalized_url + e for h in ["http://", "https://", "//", ""]
                       for w in ["www.", "m.", ""]
                       for e in endings)
    similar_urls.add(url)
    return similar_urls


def remove_same_norm_urls(urls: Iterable[str], bad_urls: Optional[Iterable[str]] = None) -> Set[str]:
    """
    Remove URLs that are HTTP/HTTPS or WWW or "/" duplicates.
    :return:
    """

    # Create a mapping of "normalized" URL to the original URL
    # NOTE: due to the way the dict comprehension works, the LAST VALUE encountered
    #       for a key will be the one kept
    norm_to_url = {normalize_url(u): u for u in urls}

    # If bad URLs provided, normalize them and remove too
    if bad_urls:
        bad_urls = set(normalize_url(u) for u in bad_urls)
        norm_to_url = {nu: u for nu, u in norm_to_url.items() if nu not in bad_urls}

    # The values of this mapping are unique by canonical URL
    return set(norm_to_url.values())


def deduplicate_urls(urls: Iterable[str],
                     root_url: str = None,
                     exclude_root: bool = False,
                     canonize: bool = False,
                     bad_patterns: Optional[Iterable[str]] = None
                     ) -> Set[str]:
    """
    Deduplicate URLs (and fully canonize, if needed, including correcting relative URLs).
    """

    # (1) First remove duplicate URLs, according to their "normalized" version
    #     (e.g. URLs that are HTTP/HTTPS or WWW or "/" duplicates)
    urls = remove_same_norm_urls(urls)

    # (2) Remove URLs with bad patterns
    if bad_patterns:
        urls = [u for u in urls if not any(bad in u.lower() for bad in bad_patterns)]

    # (3) Canonize (correct) the URLs, including making relatives absolute
    if canonize:
        urls = [canonize_url(u, root_url=root_url) for u in urls]

    # (4) Remove root URL, if need be
    if exclude_root:
        urls = [u for u in urls if u != root_url]

    return set(u for u in urls if u)


def link2email(url: str) -> str:
    if "?" not in url:
        url += "?"

    return url + "utm_source"


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
