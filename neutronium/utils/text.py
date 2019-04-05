
import difflib
import random
import re
import string
from typing import List, Optional

from inflection import singularize, pluralize
from unidecode import unidecode


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


# Regular expression pattern to remove UTF-8 greater than 3 bytes
re_pattern_utf8_fix = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
def remove_4_byte_unicode(text):
    return re_pattern_utf8_fix.sub(u'\uFFFD', text)


char_replacement_dict = {
    # Add spaces before and after dashes
    '—': ' — ',
    # Fix weird hyphens
    '‐': '-',
    # Fix footnote numbers
    '⁽': '(',
    '⁾': ')',
    '¹': '1',
    # '²': '2',
    '³': '3',
    # Fix weird single quote marks
    '‘': "'",
    '’': "'",
    '': "'",
    '': "'",
    # Fix directional double quote marks, remembering to add
    # spaces before/after (double spaces removed later)
    # '“': ' "',
    '“': '"',
    # '”.': '". ',
    # '”,': '", ',
    # '”;': '"; ',
    # '”': '" ',
    '”': '"',
    # Remove asterisks
    '*': None,
    # Fix "percent"
    # "per cent": "percent",
    # Remove (TM), (R), (c)
    # '(TM)': None,
    # '(tm)': None,
    '™': None,
    '®': None,
    '©': None,
    # Fix ellipses
    '…': '...',
    # Normalize newlines
    '\r': None,
}
string_replacement_dict = {
    # Standardize "hyphens with spaces"
    ' - ': ' — ',
    # Fix directional double quote marks, remembering to add
    # spaces before/after (double spaces removed later)
    # '”.': '". ',
    # '”,': '", ',
    # '”;': '"; ',
    # If there's a comma/period followed by a double quote,
    # then insert a space (double spaces removed later)
    # '."': '." ',
    # ',"': '," ',
    # ';"': ';" ',
    # Fix "percent"
    "per cent": "percent",
    # Remove (TM), (R), (c)
    '(TM)': "",
    '(tm)': "",
    '(R)': "",
    '(r)': "",
    '(C)': "",
    '(c)': "",
}
ord_replacement_dict = {ord(k): v for k, v in char_replacement_dict.items()}
def replace_single_chars(text):
    return text.translate(ord_replacement_dict)


def normalize_web_text(text: str, strip: bool = True) -> str:
    """
    Normalize text downloaded from the web. This does slightly more
    than normalizing text for NLP (e.g removes emojis).
    
    Actions:
    - Strip text
    - Normalize for NLP (bunch of stuff)
    - Remove non UTF-8 characters (i.e. 4 byte characters like emojis)
    - Replace multi-spaces with single space
    :return:
    """

    if not text:
        return ''

    # If there's a comma/period followed by a double quote, followed
    # by NO SPACE, then insert a space
    # text = re.sub(r'([.,])"([^\s])', r'\g<1>" \g<2>', text)

    # Fix double periods
    # text = re.sub(r'(\w)\.\.(\s)', '\g<1>.\g<2>', text)

    # Perform simple replacements
    text = replace_single_chars(text)

    # Perform complex replacements
    for orig, repl in string_replacement_dict.items():
        text = text.replace(orig, repl)

    # Fix spacing
    # text = text.replace("  ", " ")
    # text = text.replace(" \n", "\n")
    if strip:
        text = text.strip()

    # Remove 4 byte characters
    return remove_4_byte_unicode(text)


def normalize_immediately_after_download(text: str) -> str:
    # Remove the bad space characters
    text = text.translate({
        ord(u'\xa0'): None,
        ord(u'\xad'): '-'
    })

    # Remove other bad characters
    text = re.sub(r"[\x00-\x08\x0b\x0e-\x1f\x7f]", "", text)

    return text


def strip_insignificant_text_lines(text: str,
                                   bad_needles: Optional[List[str]] = None
                                   ) -> str:
    """
    Strip out short lines and lines with few letters.
    Optionally, also strip out short lines that contain one or more
    of the "bad needles" list provided.
    """

    if not text:
        raise ValueError("Need text to normalize")

    # Init the "bad needles"
    bad_needles = bad_needles or []

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

        # Lines with too few words that contain bad terms, if needed
        words = line.split(' ')
        if len(words) < 11 and bad_needles and any(s in line.lower() for s in bad_needles):
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


def experiments():
    """Conclusion - use text.translate() and text.replace()! """
    random_strings = [''.join(random.choices(string.ascii_lowercase + " -", k=20000)) for i in range(1000)]
    # random_strings_as_lists = [list(s) for s in random_strings]
    replace_count = 1
    orig = random.choices(string.ascii_uppercase, k=replace_count)
    repl = random.choices(string.ascii_letters, k=replace_count)
    repl_ord_dict = {ord(o): repl[i] for i, o in enumerate(orig)}
    repl_dict = {o: repl[i] for i, o in enumerate(orig)}
    repl_func = make_multiple_replace_func(repl_dict)
    import time
    now = time.time()
    for i, o in enumerate(orig):
        new_1 = [s.replace(o, repl[i]) for s in random_strings]
    prev = now
    now = time.time()
    print("REPLA", now - prev)
    new_2 = [s.translate(repl_ord_dict) for s in random_strings]
    prev = now
    now = time.time()
    print("TRANS", now - prev)
    # new_3 = [re.sub("|".join(orig), lambda m: repl_dict[m.group(0)], s) for s in random_strings]
    new_3 = [re.sub("|".join(orig), "x", s) for s in random_strings]
    prev = now
    now = time.time()
    print("RE", now - prev)
    # # new_4 = [re.sub(r"[c]", "?", s) for s in random_strings]
    # new_4 = [re.sub(r'(\w)-(\w)', r'\g<1>\g<2>', s) for s in random_strings]
    new_4 = [repl_func(s) for s in random_strings]
    prev = now
    now = time.time()
    print("RE_M", now - prev)
    new_5 = [" ".join(p for p in s.split(" ") if p) for s in random_strings]
    prev = now
    now = time.time()
    print("SPLIT", now - prev)
    # rx = re.compile("c")
    # new_5 = [re.sub(r"[c]", "?", s) for s in random_strings_as_lists for c in s]
    # prev = now
    # now = time.time()
    # print("LIST", now - prev)
    # print(new_1)
    # print(new_2)
