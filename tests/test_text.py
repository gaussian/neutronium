import string
import unittest

from neutronium.utils.text import create_random_string, normalize_web_text


def test_create_random_string_length_and_charset():
    s = create_random_string(24)
    assert len(s) == 24
    allowed = set(string.ascii_letters + string.digits)
    assert set(s) <= allowed
    # SystemRandom-backed: two calls should essentially never collide
    assert create_random_string(24) != create_random_string(24)


class TextUtilsTestCase(unittest.TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

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
            (
                "Everyone had an alibi-except John.",
                "Everyone had an alibi-except John.",
            ),
        ]

        for text, desired_output in data:
            self.assertEqual(normalize_web_text(text), desired_output)
