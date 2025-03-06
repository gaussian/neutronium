import unittest

from django.test import tag

from neutron.utils.text import normalize_web_text


class TextUtilsTestCase(unittest.TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    @tag("fast", "infrastructure")
    def test_can_normalize_text(self):
        data = [
            ("Hello(R)", "Hello"),
            ("..Hello©", "..Hello"),
            (
                '\n\nthis is some text," said the man…\n\n\r\n',
                'this is some text," said the man...',
            ),
            (
                '"Nothing wrong with Nancy’s cough,"\n\nI said - leaning in',
                '"Nothing wrong with Nancy\'s cough,"\n\nI said — leaning in',
            ),
            (
                "Everyone had an alibi—except John.",
                "Everyone had an alibi — except John.",
            ),
            ("Everyone had an alibi-except John.", "Everyone had an alibi-except John."),
        ]

        for text, desired_output in data:
            self.assertEqual(normalize_web_text(text), desired_output)
