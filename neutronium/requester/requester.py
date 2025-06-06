import re
import time
from typing import Optional

import idna
import requests
from django.core.exceptions import ValidationError
from django.conf import settings
from celery.exceptions import WorkerTerminate
from requests.structures import CaseInsensitiveDict

from neutron.utils.text import normalize_chars
from neutron.utils.logging import log_third_party_error, log_sys_exception
from neutron.utils.url import canonize_url, rebuild_url, parse_url

try:
    import requests_cache
except ImportError:
    requests_cache = None


class Requester:
    def __init__(
        self,
        timeout: int = 30,
        log_context: str = "N/A",
        session: Optional[requests.Session] = None,
        requests_cache_key: Optional[str] = None,
        **kwargs,
    ):

        self.timeout = timeout
        self.log_context = log_context
        self.try_optimize_url = kwargs.get("try_optimize_url", True)
        self.try_handle_paywall = kwargs.get("try_handle_paywall", True)
        self.raise_validation_error = kwargs.get("raise_validation_error", False)
        self.is_celery_worker = kwargs.get("is_celery_worker", False)
        self.verbose = kwargs.get("verbose", False)

        # If existing session exists, do not close it on __exit__
        self._do_not_close_session = bool(session)
        self.requests_session = session

        # Otherwise create session, cached or normal
        if not self.requests_session:
            if requests_cache and requests_cache_key:
                self.requests_session = requests_cache.CachedSession(requests_cache_key)
        if not self.requests_session:
            self.requests_session = requests.Session()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if not self._do_not_close_session:
            self.requests_session.close()

    def get(
        self,
        url: str,
        existing_response: Optional[requests.Response] = None,
        referer: Optional[str] = None,
    ) -> tuple[str, bytes, str, str, int, Optional[str]]:

        # Get response (connection still open, content NOT consumed)
        original_url = url
        open_response, success = self._get_open_with_retry(
            url=original_url,
            existing_response=existing_response,
            allow_retry=False,
            referer=referer,
        )

        # Wrapper to catch content consumption errors and close connection
        new_url = None
        try:

            # Get response metadata
            new_url, content_type, content_length = self._get_response_meta(open_response)
            new_url = new_url or original_url

            # Special handling to detect login/paywall pages
            if self.try_handle_paywall:
                pre_wall_url = self.check_for_wall(open_response, new_url)
                # If detected return empty, but with the pre-redirect URL
                if pre_wall_url:
                    pre_wall_url = canonize_url(pre_wall_url)
                    if self.verbose:
                        print(f"URL wall hit: {new_url}, from: {pre_wall_url}")
                    return None, None, pre_wall_url, None, 0, "wall"

            # If we are trying to optimize the URL, try getting a response with a more AGGRESSIVELY
            # stripped URL (remove all but most essential querystrings, remove URL fragments) and
            # check if the response seems to be the same (check just the content length)
            if self.try_optimize_url and success and content_length:
                optimized_url = rebuild_url(new_url, aggression=2)
                if optimized_url != new_url and optimized_url != original_url:
                    opt_open_response, opt_success = self._get_open_with_retry(
                        url=optimized_url,
                        existing_response=existing_response,
                        allow_retry=False,
                        referer=referer,
                    )
                    optimized_url, _, opt_content_length = self._get_response_meta(
                        opt_open_response
                    )
                    # Both URLs have the same response content length - we can assume they are the same
                    if (
                        optimized_url
                        and opt_success
                        and opt_content_length == content_length
                    ):
                        if self.verbose:
                            print(
                                f"URL optimization SUCCESS: {optimized_url} (old = {new_url})"
                            )
                        invalid_response = open_response
                        new_url, open_response, success = (
                            optimized_url,
                            opt_open_response,
                            opt_success,
                        )
                    # Failed to optimize
                    else:
                        if self.verbose:
                            print(
                                f"URL optimization FAIL: {optimized_url} (old = {new_url})"
                            )
                        invalid_response = opt_open_response
                    # Close whichever response we are no longer using
                    if invalid_response:
                        invalid_response.close()

            # Check headers for "no index" tags (before consuming content)
            text, content, error_code = None, None, None
            if open_response and success:
                if self.is_no_index_headers(open_response.headers):
                    error_code = "noindex"
                    success = False

            # Read (consume) the content then return
            if open_response and success:

                # If encoding type is not guessed to be UTF-8, evaluate the "apparent encoding"
                # using chardet (via open_response.apparent_encoding)
                if (
                    isinstance(open_response.encoding, str)
                    and open_response.encoding.lower().replace("-", "") != "utf8"
                ):
                    open_response.encoding = open_response.apparent_encoding

                # Pull content, simple normalization
                content = open_response.content
                text = open_response.text.strip()
                text = normalize_chars(text)

                # If content length wasn't set, set it here
                content_length = content_length or len(content)

                # Quickly see if we can pull a canonical URL out of the text
                new_url = (
                    self.get_canonical_link_from_html(text, current_url=new_url)
                    or new_url
                )

                # Quickly check text if this is a "no index" page
                if self.is_no_index_html(text):
                    error_code = "noindex"

            return text, content, new_url, content_type, content_length, error_code

        # Error in content consumption
        except requests.exceptions.RequestException as e:
            # Perhaps wrong content encoding was assumed?
            # NOTE: content encoding (e.g. gzip) IS NOT encoding type (e.g. UTF-8)!
            # if "gzip" in e.strerror:
            #     try:
            #         open_response.headers["Accept-Encoding"] = "deflate"
            #         content = open_response.content
            #         text = open_response.text
            #         text = normalize_chars(text)
            #     except requests.exceptions.RequestException as e:
            #         pass
            log_third_party_error(
                f"Content consumption failed for {original_url}, exception = {e} ({e.strerror})"
            )
            if open_response:
                open_response.close()
            return None, None, new_url or original_url, None, 0, "content"

        # Close the connection
        finally:
            if open_response:
                open_response.close()

    def _get_open_with_retry(
        self,
        url: str,
        allow_retry: bool,
        use_user_agent: bool = True,
        existing_response: Optional[requests.Response] = None,
        referer: Optional[str] = None,
    ) -> tuple[requests.Response, bool]:

        # Shorthand for retrying this function with user agent
        def close_and_retry_if_have_not_yet(
            old_response: requests.Response, new_url: Optional[str] = None
        ) -> tuple[requests.Response, bool]:

            # Close the old response first
            if old_response:
                old_response.close()

            # Update URL if needed
            new_url = new_url or url

            # If haven't retried, retry with user agent (wait a second first)
            if allow_retry:
                time.sleep(1)
                print(f"Retrying: {url}")
                return self._get_open_with_retry(
                    url=new_url, allow_retry=False, use_user_agent=True, referer=referer
                )

            # Otherwise failed
            return None, False

        # Existing response
        response = existing_response

        print_error = False
        log_error = False
        error_message = None

        try:

            # Existing response, no need to fetch, otherwise fetch
            if response:
                pass

            # Do GET request, adding user agent if this is a retry
            else:
                extra_kwargs = {"headers": dict()}
                if use_user_agent:
                    extra_kwargs["headers"]["User-Agent"] = settings.BOT_USER_AGENT
                if referer:
                    extra_kwargs["headers"]["Referer"] = referer
                # Add scheme if missing
                if url.startswith("//"):
                    url = "http:" + url
                response = self.requests_session.get(
                    url, timeout=self.timeout, stream=True, **extra_kwargs
                )

            # If we get a 403 or 405, try again with the User Agent if we haven't yet
            status_code = response.status_code
            if status_code in (403, 405):
                response, success = close_and_retry_if_have_not_yet(response)
                if response:
                    status_code = response.status_code

            # If we get any other 300+, error (print, don't log)
            if status_code >= 300:
                success = False
                error_message = f"Bad response code downloading {url} ({self.log_context}), code: {status_code}"
                print_error = True

            # We received a 200 response - we're nearly OK...
            else:
                try:

                    # We used "stream" mode, so content hasn't been read yet - make
                    # sure it isn't too big
                    # TODO: make this more general
                    content_length = int(response.headers.get("content-length", 0))
                    if content_length > settings.MAX_REQUEST_CONTENT_SIZE:
                        success = False
                        error_message = f"Content too big from {url} ({self.log_context}), size: {content_length}"
                        log_error = True
                        allow_retry = True  # need this to log error without recursing

                    # If we've reached here with no exceptions, we have success
                    else:
                        success = True

                # Bad content length
                except ValueError as e:
                    success = False
                    error_message = str(e)
                    log_error = True

        # Memory allocation failure, CRITICAL FAIL (TERMINATE WORKER if we are in one)
        # TODO: is termination the right call? what if we get stuck in a loop downloading
        #       a file that won't fit in memory?
        except MemoryError as e:
            error_message = (
                f"Memory error downloading {url} ({self.log_context}), detail: {e}"
            )
            log_sys_exception(error_message)
            if self.is_celery_worker:
                raise WorkerTerminate(error_message)
            raise

        # Too many redirects (don't retry, print don't log)
        except requests.exceptions.TooManyRedirects as e:
            success = False
            error_message = f"Too many redirects while downloading {url} ({self.log_context}), detail: {e}"
            print_error = True
            allow_retry = True  # need this to log error without recursing

        # Request timeout (don't retry, print don't log)
        except requests.exceptions.Timeout as e:
            response, success = close_and_retry_if_have_not_yet(response)
            if not success:
                error_message = (
                    f"Timed out downloading {url} ({self.log_context}), detail: {e}"
                )
                print_error = True

        # SSL error, try with non-HTTPS if possible
        except requests.exceptions.SSLError as e:
            if url.startswith("https:"):
                non_ssl_url = url.replace("https:", "http:")
                allow_retry = True  # Allow retrying even if we've disabled it
                response, success = close_and_retry_if_have_not_yet(
                    response, new_url=non_ssl_url
                )
            else:
                success = False
            if not success:
                error_message = (
                    f"SSL error while downloading {url} ({self.log_context}), detail: {e}"
                )
                log_error = True

        # Some connection error (retry)
        except requests.exceptions.ConnectionError as e:
            response, success = close_and_retry_if_have_not_yet(response)
            if not success:
                error_message = f"Connection error (not SSL-related), likely rejection, while downloading {url} ({self.log_context}), detail: {e}"
                log_error = True

        # Other request error (don't retry)
        except requests.exceptions.RequestException as e:
            success = False
            error_message = (
                f"Other request error downloading {url} ({self.log_context}), detail: {e}"
            )
            log_error = True
            allow_retry = True  # need this to log error without recursing

        # Some IDNA error
        except idna.core.IDNAError as e:
            success = False
            error_message = (
                f"IDNA error downloading {url} ({self.log_context}), detail: {e}"
            )
            log_error = True
            allow_retry = True  # need this to log error without recursing

        # Any other error (don't retry)
        except Exception as e:
            success = False
            error_message = f"Other non-requests error downloading {url} ({self.log_context}), detail: {e}"
            log_error = True
            allow_retry = True  # need this to log error without recursing

        # Error processing
        if not success:
            if print_error and error_message and allow_retry:
                print(error_message)
            if log_error and error_message and allow_retry:
                log_third_party_error(error_message)
            if self.raise_validation_error:
                raise ValidationError(error_message)

        return response, success

    @staticmethod
    def _get_response_meta(response: requests.Response) -> (str, str, int):
        url, content_type, content_length = None, None, 0

        if response:

            # URL (canonize it to remove bad URL params)
            url = canonize_url(response.url)

            # Content length
            try:
                content_length = int(response.headers.get("content-length", 0))
            except ValueError:
                content_length = 0

            # Content type
            content_type = response.headers.get("content-type", None)

        return url, content_type, content_length

    @staticmethod
    def check_for_wall(response: requests.Response, new_url: str) -> Optional[str]:
        """
        We suspect there might be a login/paywall page if ALL of the following:
        (1) we were redirected, with a TEMPORARY redirect
        (2) the pre-redirect URL seems much more "complex" than the final URL:
            - final URL has only 1-2 slashes
            - pre URL has 2+ more slashes than final URL
            - final URL has significantly longer querystring or contains a likely paywall redirect link

        Return the pre-wall link, or None if there was no wall.
        """

        if (
            response
            and len(response.history)
            and not response.history[-1].is_permanent_redirect
        ):
            url_pre = response.history[-1].url
            url_obj_pre = parse_url(url_pre)
            url_obj_post = parse_url(new_url)
            slash_count_pre = url_obj_pre.path.count("/")
            slash_count_post = url_obj_post.path.count("/")
            if "barrier=" in url_obj_post.query:
                return url_pre
            if (
                slash_count_post <= 2
                and slash_count_pre >= slash_count_post + 2
                and (
                    len(url_obj_post.query) >= len(url_obj_pre.query) + 10
                    or any(f in url_obj_post.query for f in ("url=", "redirect"))
                )
            ):
                return url_pre

        return None

    @staticmethod
    def get_canonical_link_from_html(html: str, current_url: str) -> Optional[str]:
        """
        Return the article's canonical URL (quick and dirty), either:
        - the rel=canonical tag
        - the og:url tag
        """

        # Helper
        def find_url(frag, attr):
            # Quick and dirty check
            start_idx = html.find(frag)
            if start_idx != -1:
                end_idx = html.find(">", start_idx, start_idx + 300)
                if end_idx != -1:
                    # Regex search on small chunk of text
                    matches = re.findall(attr + r"=\"([^\s]+)\"", html[start_idx:end_idx])
                    if matches:
                        # Canonize if found, passing in the current URL as the root (this will
                        # correct relative URLs)
                        new_url = canonize_url(matches[0], root_url=current_url)
                        if new_url:
                            return new_url
            return None

        if not html or html.startswith("<?xml"):
            return None

        # Canonical link
        url = find_url('rel="canonical"', "href")

        # OG URL (if failed above)
        url = url or find_url('property="og:url"', "content")

        return url

    @staticmethod
    def is_no_index_headers(headers: CaseInsensitiveDict) -> bool:
        """
        Check if this is a "no index" page, defined by the robots headers
        """
        return headers.get("X-Robots-Tag", None) in ("noindex", "all")

    @staticmethod
    def is_no_index_html(html: str) -> bool:
        """
        Check if this HTML is a "no index" page, defined by the robots meta tag
        """

        if not html or html.startswith("<?xml"):
            return False

        bad_fragments = (
            'content="noindex"',
            'content="all"',
        )
        return any(f in html for f in bad_fragments)
