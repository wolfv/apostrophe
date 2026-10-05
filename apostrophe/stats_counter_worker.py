# Copyright (C) 2026, Manuel Genovés <manuel.genoves@gmail.com>
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
# END LICENSE

"""Worker used to calculate document statistics."""

import regex as re

from apostrophe.markup_regex import (BOLD, BOLD_ITALIC, BLOCK_QUOTE,
                                     CODE_BLOCK, FOOTNOTE, FOOTNOTE_ID,
                                     HEADER, HEADER_UNDER, HORIZONTAL_RULE,
                                     IMAGE, ITALIC_ASTERISK, ITALIC_UNDERSCORE,
                                     LINK, LINK_ALT, LIST, MATH, ORDERED_LIST,
                                     STRIKETHROUGH, TABLE)


# Regexp that matches any character,
# except for newlines and subsequent spaces.
CHARACTERS = re.compile(r"[^\s]|(?:[^\S\n](?!\s))")

# Regexp that matches Asian letters, general symbols and hieroglyphs,
# as well as sequences of word characters optionally containing non-word
# characters in-between.
WORDS = re.compile(r"[\u3040-\uffff]|(?:\w+\S?\w*)+", re.UNICODE)

# Regexp that matches sentence-ending punctuation characters, ie.
# full stop, question mark, exclamation mark, paragraph, and variants.
SENTENCES = re.compile(r"[^\n][.。।෴۔።?՞;⸮؟？፧꘏⳺⳻⁇﹖⁈⁉‽!﹗！՜߹႟᥄\n]+")

# Regexp that matches paragraphs, ie.
# anything separated by at least 2 newlines.
PARAGRAPHS = re.compile(r"(?:[^\n]+\n?)+(?=\n{2,}|\Z)")

# List of regexp whose matches should be replaced by their "text" group.
# Order is important.
MARKUP_REGEXP_REPLACE = (
    BOLD_ITALIC, ITALIC_ASTERISK, ITALIC_UNDERSCORE, BOLD, STRIKETHROUGH,
    IMAGE, LINK, LINK_ALT, LIST, ORDERED_LIST, BLOCK_QUOTE, HEADER,
    HEADER_UNDER, CODE_BLOCK, TABLE, MATH, FOOTNOTE_ID, FOOTNOTE
)

# List of regexp whose matches should be removed. Order is important.
MARKUP_REGEXP_REMOVE = (HORIZONTAL_RULE,)


def count_worker(child_conn):
    """Count statistics for text received over ``child_conn``.

    The result is in the format
    (characters, words, sentences, (hours, minutes, seconds))
    """

    while True:
        while True:
            try:
                text = child_conn.recv()
                if not child_conn.poll():
                    break
            except EOFError:
                child_conn.close()
                return

        for regexp in MARKUP_REGEXP_REPLACE:
            text = re.sub(regexp, r"\g<text>", text)
        for regexp in MARKUP_REGEXP_REMOVE:
            text = re.sub(regexp, "", text)

        character_count = len(re.findall(CHARACTERS, text))
        word_count = len(re.findall(WORDS, text))
        sentence_count = len(re.findall(SENTENCES, text))
        paragraph_count = len(re.findall(PARAGRAPHS, text))

        read_m, read_s = divmod(word_count / 200 * 60, 60)
        read_h, read_m = divmod(read_m, 60)
        read_time = (int(read_h), int(read_m), int(read_s))

        child_conn.send((character_count, word_count, sentence_count,
                         paragraph_count, read_time))
