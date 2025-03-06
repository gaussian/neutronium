import unittest

from django.test import tag

from .requester import Requester


class RequestUtilsTestCase(unittest.TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    @tag("fast", "infrastructure")
    def test_can_optimize_url(self):
        data = [
            # TODO: no longer works, as NYT thinks we've blocked Javascript/ads
            # ("https://www.nytimes.com/2014/03/29/business/a-florida-engineer-unlocked-the-mystery-of-gms-ignition-flaw.html?_r=2",
            #  "https://www.nytimes.com/2014/03/29/business/a-florida-engineer-unlocked-the-mystery-of-gms-ignition-flaw.html",
            #  None),
            (
                "https://money.cnn.com/2007/09/26/news/companies/uaw_gm_deal/index.htm?postversion=2007092604",
                "https://money.cnn.com/2007/09/26/news/companies/uaw_gm_deal/index.htm",
                None,
            ),
            (
                "https://money.cnn.com/2007/09/24/news/companies/gm_uaw_strikedeadline/?postversion=2007092412",
                "https://money.cnn.com/2007/09/24/news/companies/gm_uaw_strikedeadline/",
                None,
            ),
            (
                "https://www.law360.com/commercialcontracts/articles/1241729/contractor-must-face-ex-nfler-s-dream-house-ip-claims",
                "https://www.law360.com/articles/1241729/contractor-must-face-ex-nfler-s-dream-house-ip-claims",
                None,
            ),
            # TODO: this results in an SSL error, despite not using SSL...so can't use this anymore
            # ("http://www.pyxisintel.com",
            #  "https://www.bain.com/industry-expertise/private-equity/pyxis/",
            #  None),
            # Bloomberg should show a paywall or bot-catcher, and we should recognize this
            # TODO: Bloomberg no longer shows a paywall here, so this test fails
            # ("https://www.bloomberg.com/news/articles/2020-07-09/wells-fargo-is-readying-thousands-of-job-cuts-to-start-this-year?utm_source=email",
            #  "https://www.bloomberg.com/news/articles/2020-07-09/wells-fargo-is-readying-thousands-of-job-cuts-to-start-this-year",
            #  "wall"),
        ]

        r = Requester(try_optimize_url=True, verbose=True)
        for url, canonical_url, correct_error_code in data:
            _, _, new_url, _, _, error_code = r.get(url)
            self.assertEqual(new_url, canonical_url)
            self.assertEqual(error_code, correct_error_code, url)
