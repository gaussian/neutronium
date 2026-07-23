from unittest.mock import MagicMock

import pytest
import requests

from neutronium.requester import Requester, RequesterError


def _requester_with_failing_session(**kwargs):
    """A Requester whose session always raises a connection error on GET."""
    session = MagicMock()
    session.get.side_effect = requests.exceptions.ConnectionError("boom")
    return Requester(
        session=session, try_optimize_url=False, try_handle_paywall=False, **kwargs
    )


def test_requester_error_is_exception():
    assert issubclass(RequesterError, Exception)


def test_raises_requester_error_when_flag_set():
    with _requester_with_failing_session(raise_validation_error=True) as r:
        with pytest.raises(RequesterError):
            r.get("http://example.com")


def test_returns_empty_result_without_flag():
    with _requester_with_failing_session() as r:
        text, content, *_rest, error_code = r.get("http://example.com")
    assert text is None
    assert content is None
