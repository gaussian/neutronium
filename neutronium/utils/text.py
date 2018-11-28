
import difflib
import random
import re
import string
from typing import List

from django.conf import settings
from inflection import singularize, pluralize
from unidecode import unidecode

from neutron.utils.iterable import multi_needle_search


def multiple_replace(text, replace_dict, flags=0) -> str:
    """From https://www.safaribooksonline.com/library/view/python-cookbook-2nd/0596007973/ch01s19.html"""
    rx = re.compile('|'.join(map(re.escape, replace_dict)), flags)
    return rx.sub(lambda match: replace_dict[match.group(0)], text)


def make_multiple_replace_func(*args, **kwargs):
    """From https://www.safaribooksonline.com/library/view/python-cookbook-2nd/0596007973/ch01s19.html"""
    replace_dict = dict(*args, **kwargs)
    rx = re.compile('|'.join(map(re.escape, replace_dict)))
    def xlat(text):
        return rx.sub(lambda match: replace_dict[match.group(0)], text)
    return xlat


multiple_replace_nlp = None
multiple_replace_bad_texts = None


def random_string(num_chars):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(num_chars))


def unicode_normalize(text, lowercase):
    if lowercase:
        text = text.lower()

    return unidecode(text.strip())


def rchop(text, ending):
    if text.endswith(ending):
        return text[:-len(ending)]
    return text


def normalize_for_nlp(text: str):
    global multiple_replace_nlp

    # Normalize double quote characters
    if '“' in text or '”' in text:
        text = re.sub(r'([^\s])“', '\g<1> "', text)  # any non whitespace followed by opening quote
        text = re.sub(r'”([^\s])', '" \g<1>', text)  # any closing quote followed by non whitespace
        # NOTE: turning “ or ” into " occurs in the multiple_replace below!
        # text = re.sub(r'[“”]', '"', text)

    # If there's a comma/period followed by a double quote, followed
    # by NO SPACE, then insert a space
    text = re.sub(r'([.,])"([^\s])', '\g<1>" \g<2>', text)

    # Add spaces before and after dashes
    # TODO: when move to SpaCy, should be able to remove this...?
    if '—' in text:
        text = re.sub(r'(\w)—', '\g<1> —', text)
        text = re.sub(r'—(\w)', '— \g<1>', text)

    # Remove hyphens within words
    # TODO: when move to SpaCy, what happens here
    # if '-' in text:
    #     text = re.sub(r'(\w)-(\w)', '\g<1> \g<2>', text)

    # Fix double periods
    # text = re.sub(r'(\w)\.\.(\s)', '\g<1>.\g<2>', text)

    # Perform simple replacements (in 1 pass)
    if not multiple_replace_nlp:
        multiple_replace_nlp = make_multiple_replace_func({
            # Fix weird quotations
            '‘': "'",
            '’': "'",
            '': "'",
            '': "'",
            '“': '"',
            '”': '"',
            # Remove asterisks
            '*': '',
            # Fix "percent"
            "per cent": "percent",
            # Remove (TM), (R)
            '(TM)': '',
            '(tm)': '',
            '(R)': '',
            '(r)': '',
            # Fix ellipses
            '…': '...',
            # Normalize newlines
            "\r\n": "\n",
        })
    return multiple_replace_nlp(text)


# TODO: WHY IS THIS WEIRD
def normalize_for_nlp_weird(text: str) -> str:
    text = normalize_for_nlp(text)
    if '\'' in text:
        text = re.sub(r'(^|\s)\'', '\g<1>\' ', text)
    return text


# Regular expression pattern to remove UTF-8 greater than 3 bytes
re_pattern_utf8_fix = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)


def normalize_web_text(text: str) -> str:
    """
    Normalize text downloaded from the web. This does slightly more
    than normalizing text for NLP (e.g removes emojis).
    
    Actions:
    - Strip text
    - Normalize for NLP (see above)
    - Remove non UTF-8 characters (i.e. 4 byte characters like emojis)
    - Replace multi-spaces with single space
    - Remove bad text (from Django settings)
    :param text: 
    :return: 
    """

    global multiple_replace_bad_texts

    if not text:
        return ''

    text = normalize_for_nlp(text.strip())
    text = re_pattern_utf8_fix.sub(u'\uFFFD', text)
    text = ' '.join(text.split(' '))
    if not multiple_replace_bad_texts:
        multiple_replace_bad_texts = make_multiple_replace_func(dict(zip(
            settings.BAD_TEXTS, [" - "] * len(settings.BAD_TEXTS)
        )))
    return multiple_replace_bad_texts(text)


def normalize_immediately_after_download(text: str) -> str:
    # Remove newlines in XML, as well as bad space characters
    # if text.startswith("<"):
    #     text = re.sub(r"[\xa0\n]]", " ", text)
    #
    # # If not HTML, just remove the bad space characters
    # else:
    text = text.replace(u'\xa0', u' ')

    # Remove other bad characters
    text = re.sub(r"[\x00-\x08\x0b\x0e-\x1f\x7f]", "", text)

    return text


def normalize_stripping_insignificant_text_lines(text: str, bad_needles: List[str]=None) -> str:
    """
    Strip out short lines and lines with few letters and words.
    Optionally, also strip out any lines that contain one or more
    of the "bad needles" list provided.
    """

    # Init the "bad needles"
    bad_needles = bad_needles or None

    # Split into lines
    lines = text.split("\n")
    lines_to_keep = []
    for line in lines:

        # Short lines
        if len(line) < 8:
            continue

        # Lines with too few letters
        if sum(c.isalpha() for c in line) < 5:
            continue

        # [HACK] Strip bad chars here
        line = line.strip().replace(u'\xa0', u' ')

        # Lines with too few words
        words = line.split(' ')
        if len(words) < 11:
            continue

        # Lines containing bad terms, if needed
        if bad_needles and multi_needle_search(line.lower(), bad_needles):
            continue

        # Not a bad line - append it to the list
        lines_to_keep.append(line)

    return "\n\n".join(lines_to_keep)


def strip_problematic_sec_tags(html: str) -> str:
    tags_to_remove = re.compile(r'('
                                #r'style="[^>]*"|'
                                r'<\s*font\s*.*?>|<\s*/font\s*>|'
                                r'<\s*a\s*.*?>|<\s*/a\s*>|'
                                r'<\s*b\s*.*?>|<\s*/b\s*>|'
                                r'<\s*em\s*.*?>|<\s*/em\s*>|'
                                r'<\s*i\s*.*?>|<\s*/i\s*>|'
                                r'<\s*sup\s*.*?<\s*/sup\s*>'
                                r')', flags=re.IGNORECASE)
    html = re.sub(tags_to_remove, '', html)
    return html


def is_capitalized_word_list(words):
    """
    Check if every word starts with a capital letter.
    Proxy for being a named entity (in addition to the other named entity recognition stuff.
    """
    for word in words:
        if word[0].isalpha() and not word[0].isupper():
            return False
    return True


def is_capitalized_phrase(phrase):
    """
    Check if every word starts with a capital letter.
    Proxy for being a named entity (in addition to the other named entity recognition stuff.
    """
    return is_capitalized_word_list(phrase.split(' '))


def is_quote(character):
    if character == '\'' or character == '"' or character == '’' or character == '”' or character == '“':
        return True
    return False


def ratio_newline_digit(text):
    """
    Get the fraction of this text's characters that are NEWLINE or DIGIT
    :param text: 
    :return: 
    """
    num_newlines = num_digits = 0
    for char in text:
        if char == '\n':
            num_newlines += 1
        if char.isdigit():
            num_digits += 1
    return (num_newlines + num_digits) / len(text)


def sentence_similarity(one, two):
    return difflib.SequenceMatcher(None, one, two).ratio()


def camel_case_split(identifier):
    """From https://stackoverflow.com/a/29920015"""
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]


def split_iter_word(text):
    return (x.group(0) for x in re.finditer(r"[^ \n]+", text))


def split_iter_para_bracket(text):
    return (x.group(0) for x in re.finditer(r"[^\n()\[\]]+", text))


def split_iter_line_with_min(text, min_length):
    start = 0
    while start < len(text):
        end = text.find('\n', start + min_length) + 1       # returns -1 if not found, so end + 1 == 0
        if end == 0:
            end = len(text)
        yield text[start:end]
        start = end


def word_count(thestring):
    return len(thestring.split(' '))


def get_lang_if_not_english(url):
    """
    Get the language code, if looks like URL is not English (None otherwise)
    :param url: 
    :return: 
    """
    non_english_codes = [
        'es', 'ja', 'zh', 'zh-CN', 'zh-HK', 'nl', 'pt', 'it', 'fr', 'de', 'ko'
    ]

    # Search URL for the codwes
    for code in non_english_codes:
        if '/' + code + '/' in url:
            return code
    return None


# NOTE: this is simpler whan using morphy...
def build_rough_set_with_plurals_and_singulars(words):

    # Add all existing words
    output = set(words)

    # Add plural or singular versions
    for word in words:
        output.add(singularize(word))
        output.add(pluralize(word))
        # if word.endswith('ies'):
        #     output.add(word[:-3] + 'y')
        # elif word.endswith('y'):
        #     output.add(word[:-1] + 'ies')
        # elif word.endswith('es'):
        #     output.add(word[:-2])
        # elif word.endswith('ss'):
        #     output.add(word + 'es')
        # elif word.endswith('s'):
        #     output.add(word[:-1])
        # else:
        #     output.add(word + 's')

    return output


def build_set_with_without_hyphens(words):
    output = set()
    for word in words:
        output.add(word.replace(" ", "-"))
        output.add(word.replace("-", " "))
    return output


# TODO: check this logic
def uncapitalize_start_of_sentence(text):
    if text[0].isupper() and not text[1].isupper() and text[1] != '.':
        return text[0].lower() + text[1:]
    elif is_quote(text[0]) and text[1].isupper():
        return text[0] + text[1].lower() + text[2:]
    return text
