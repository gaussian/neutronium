
import difflib
import random
import re
import string
from collections import Counter
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
    '': ' — ',
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
    '\x92': "'",
    # Fix directional double quote marks, remembering to add
    # spaces before/after (double spaces removed later)
    # '“': ' "',
    '“': '"',
    # '”.': '". ',
    # '”,': '", ',
    # '”;': '"; ',
    # '”': '" ',
    '”': '"',
    '': '"',
    '': '"',
    # Remove asterisks
    # '*': None,
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
        return ""

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


unicode_space_replacement_dict = {
    "\x95": "•",
    "\xa0": " ",
    "\u00a0": " ",
    "\xad": "-",
    "\u0096": "-",
    "\u00ad": "-",
    "\u1680": "-",
    "\u180e": None,
    "\u2000": " ",
    "\u2001": " ",
    "\u2002": " ",
    "\u2003": " ",
    "\u2004": " ",
    "\u2005": " ",
    "\u2006": " ",
    "\u2007": " ",
    "\u2008": " ",
    "\u2009": " ",
    "\u200a": " ",
    "\u200b": None,
    "\u202f": " ",
    "\u205f": " ",
    "\u3000": " ",
    "\ufeff": None,
}
ord_space_replacement_dict = {ord(k): v for k, v in unicode_space_replacement_dict.items()}
def normalize_immediately_after_download(text: str) -> str:
    # Remove/fix the bad space characters
    text = text.translate(ord_space_replacement_dict)

    # Remove other bad (ASCII) characters
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

        # Lines with too few words that contain bad terms, if needed
        line = line.strip()
        words = line.split(' ')
        if len(words) < 11 and bad_needles and any(s in line.lower() for s in bad_needles):
            continue

        # Not a bad line - append it to the list
        lines_to_keep.append(line)

    return "\n\n".join(lines_to_keep)


END_CHARS = (".", ":", "?", "!", "\"", "”", "'", "’", "")
CONSERVATIVE_END_CHARS = END_CHARS + (":",)
CURRENCIES = ("$", "€", "¥", "£")
def clean_multi_page_report(page_texts, remove_bad_lines=True):

    # Debug
    # from neutron.utils.performance import Performance
    # perf = Performance()
    # perf.print_time_since(level=3, pre_print="strt")

    # Break into lines
    lines_by_page = [[l.strip() for l in p.split("\n")] for p in page_texts]

    # Debug
    # perf.print_time_since(level=3, pre_print="splt")

    # First, remove bad lines if necessary
    if remove_bad_lines:
        for i, lines in enumerate(lines_by_page):
            # Handle short lines
            cleaned_lines = []
            for line in lines:
                if not line:
                    continue
                # fraction_non_alpha = sum(not c.isalpha() for c in line) / len(line)
                fraction_non_alpha = 1 - (sum(map(str.isalpha, line)) / len(line))
                # Remove any line that is almost completely non alpha (e.g. number strings)
                if fraction_non_alpha > 0.8:
                    continue
                # Remove super short lines
                if len(line) <= 8:
                    continue
                # Remove short lines that end in number or % or start with currency
                if len(line) <= 25 and (line[-1].isdigit() or line[-1] in ("%",) or line[0] in CURRENCIES):
                    continue
                # Remove short lines that are just parentheticals
                if len(line) <= 25 and line[0] == "(" and line[-1] == ")":
                    continue
                # Remove moderately short lines with mostly non-characters
                if len(line) <= 40 and fraction_non_alpha > 0.6:
                    continue
                # Check for short lines with mostly capitals - these could be section headers,
                # so wrap in newlines just in case
                if len(line) <= 80 and line[0].isupper():
                    if line[-1] not in END_CHARS or sum(map(str.isupper, line)) / len(line) >= 0.5:
                        line = "\n" + line + "\n"
                cleaned_lines.append(line)
            lines_by_page[i] = cleaned_lines

    # Debug
    # perf.print_time_since(level=3, pre_print="rmbd")

    # Create a list of repeated lines to remove, either:
    # (1) Page headers/footers (occurring in the first/last lines of each page)
    # (2) Very short repeated headers throughout the document
    possible_header_line_indices = [0, 1, 2, -1, -2, -3]
    non_empty_lines_by_page = [[l for l in p if l] for p in lines_by_page]
    header_lines, short_repeating_lines = set(), set()
    if remove_bad_lines:
        # Page header/footer
        possible_header_lines = [p[i] for p in non_empty_lines_by_page for i in possible_header_line_indices
                                 if i < len(p) and -i <= len(p) and p[i]]
        counter = Counter(possible_header_lines)
        header_lines = set(l for l, cnt in counter.items()
                           if (cnt >= 3 and len(l) >= 100)
                           or (cnt >= 4 and len(l) < 100))
        # Very short repeating liens
        short_lines = [l for p in non_empty_lines_by_page for l in p if len(l) <= 50]
        counter = Counter(short_lines)
        short_repeating_lines = set(l for l, cnt in counter.items() if cnt >= 3)

    # Debug
    # perf.print_time_since(level=3, pre_print="prel")

    # Check first couple pages to see if sentences have been split in the middle
    sentences_need_merging = False
    count_sentence_splits = 0
    if len(non_empty_lines_by_page) >= 3:
        start, end = 1, 3
    else:
        start, end = 0, 2
    for lines in non_empty_lines_by_page[start:end]:
        for i, line in enumerate(lines):
            # Definitely a split sentence if ALL of these are true:
            # (1) Line starts with lowercase
            # (2) Previous line ends with a non-sentence-ending character
            # (3) Previous line is long enough to be a full page width
            # (4) Line contains a specific sentence end (i.e. ". ")
            prev_line = lines[i - 1]
            if i > 0 and line[0].islower() and prev_line[-1] not in CONSERVATIVE_END_CHARS and len(prev_line) > 60 \
                    and (line[-1] == "." or ". " in line):
                count_sentence_splits += 1
                if count_sentence_splits >= 3:
                    sentences_need_merging = True
                    break
        if sentences_need_merging:
            break

    # Debug
    # perf.print_time_since(level=3, pre_print="nemg")

    # Look through each page
    final_text = ""
    prev_page_lines = None
    for i, lines in enumerate(lines_by_page):
        page_no = i + 1
        skip = False

        # Skip empty pages
        if not lines:
            skip = True

        # Skip pages that are almost entirely lots of short headers/phrases
        if len(lines) > 6 and sum(len(l) <= 80 for l in lines) / len(lines) >= 0.9:
            skip = True

        # If skipping, add some padding space and reset the "previous page"
        # so that we don't try to connect the first sentence of an upcoming
        # page to the last sentence of a previous non-consecutive page!
        if skip:
            if final_text[-1] != "\n":
                final_text += "\n"
            prev_page_lines = None
            continue

        # Remove page headers/footers
        if remove_bad_lines:
            possible_page_numbers = [str(n) for n in range(page_no - 2, page_no + 3)]
            for j in possible_header_line_indices:
                # Not enough lines to check for the jth header
                if j >= len(lines) or -j > len(lines):
                    continue
                line = lines[j]
                # Remove numbers or lines that start/end with the page number
                if len(line) < 40 and any(
                        line.isdigit() or line.startswith(f"{n} ") or line.endswith(f" {n}" or f"{n} of " in line)
                        for n in possible_page_numbers):
                    del lines[j]
                # Remove common headers/footers
                elif line in header_lines:
                    del lines[j]

        # Remove short repeating lines (if necessary)
        if remove_bad_lines:
            repeated_lines_to_remove = set()
            for j, line in enumerate(lines):
                if len(line) <= 50 and line in short_repeating_lines:
                    repeated_lines_to_remove.add(line)
            if repeated_lines_to_remove:
                lines = [l for l in lines if len(l) > 50 or not l in repeated_lines_to_remove]

        # Remove start/end empty lines (i.e. where there were multiple newlines in the original text)
        # good_lines = [l.strip() for l in lines if l]
        # start, end = 0, len(lines)
        # while start < end and not lines[start]:
        #     start += 1
        # while start < end and not lines[end - 1]:
        #     end -= 1
        # if start == end:
        #     continue
        # good_lines = [l for l in lines[start:end]]
        good_lines = [l for l in lines if l]

        # For the first page, merge consecutive lines at the top that are ALL CAPS
        # NOTE: don't merge more than 10, that's a little crazy
        if page_no == 1:
            # Find first line that is NOT uppercase, i.e. the extent of the merge
            line_index_after_all_caps = next((j for j, l in enumerate(good_lines) if not l.isupper() and j <= 10), 10)
            if line_index_after_all_caps:
                # Start from 2nd line (merge all into first line)
                for j in range(1, line_index_after_all_caps):
                    good_lines[0] += " " + good_lines[j]
                for j in range(1, line_index_after_all_caps):
                    del good_lines[j]

        # Connect to previous page, depending on whether we think there was a pagebreak
        # in the middle of a sentence
        if prev_page_lines is not None:
            prev_page_last_char = prev_page_lines[-1][-1] if prev_page_lines else None
            # We are in middle of sentence if:
            # (1) this page doesn't start with a bullet point
            # (2) prev page didn't end with a page ending character AND
            # (3) prev page wasn't a title page/cover page (i.e. prev page is first page and # lines is low)
            if good_lines[0][0] == "•":
                final_text += "\n"
            elif prev_page_last_char and prev_page_last_char not in CONSERVATIVE_END_CHARS and \
                    (page_no >= 3 or len(prev_page_lines) > 5):
                final_text += " "
            else:
                final_text += "\n\n"
        prev_page_lines = good_lines

        # Merge lines depending on whether sentences have been split
        if sentences_need_merging:
            lines_with_separators = [("" if i == 0 else
                                      (" " if l and not l.isupper() and
                                              # l[0].islower() and
                                              good_lines[i - 1] and good_lines[i - 1][-1] not in END_CHARS and
                                              len(good_lines[i - 1]) > 80 else "\n")
                                      ) + l for i, l in enumerate(good_lines)]
            page_text = "".join(lines_with_separators)
        else:
            page_text = "\n".join(good_lines)

        # Add the current page
        final_text += page_text

    # Debug
    # perf.print_time_since(level=3, pre_print="done")

    return final_text


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
