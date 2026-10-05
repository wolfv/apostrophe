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

"""Markdown parsing worker.
"""

import regex as re

from apostrophe import markup_regex
from apostrophe.markup_regex import (BLOCK_QUOTE, BOLD, BOLD_ITALIC, CODE,
                                     HEADER, HEADER_UNDER, HORIZONTAL_RULE,
                                     IMAGE, ITALIC_ASTERISK, ITALIC_UNDERSCORE,
                                     LINK, LINK_ALT, MATH, STRIKETHROUGH,
                                     TABLE)


def parse_worker(child_conn):

    while True:
        while True:
            try:
                text = child_conn.recv()
                if not child_conn.poll():
                    break
            except EOFError:
                child_conn.close()
                return

        # List of tuples in the form (tag_name, tag_args, tag_start,
        # tag_end).
        result = []
        # Find "```" code block tag (offset + colorize paragraph).
        code_blocks = []
        for match in re.finditer(markup_regex.CODE_BLOCK, text):
            start, end = match.start("block"), match.end("block")
            result.append(('code_block', (), start, end))
            code_blocks.append((start, end))

        def inside_code_blocks(start, end):
            return any(s < start < e or s < end < e
                       for s, e in code_blocks)

        # Find:
        # - "_italic_" (italic)
        # - "**bold**" (bold)
        # - "***bolditalic***" (bold/italic)
        # - "~~strikethrough~~" (strikethrough)
        # - "`code`" (colorize)
        # - "$math$" (colorize)
        # - "---" table (wrap/pixels)
        regexps = (
            (ITALIC_ASTERISK, 'italic'),
            (ITALIC_UNDERSCORE, 'italic'),
            (BOLD, 'bold'),
            (BOLD_ITALIC, 'bold_italic'),
            (STRIKETHROUGH, 'strikethrough'),
            (CODE, 'code_text'),
            (MATH, 'code_text'),
            (TABLE, 'wrap_none'),
        )
        for regexp, tag_name in regexps:
            for match in re.finditer(regexp, text):
                if not inside_code_blocks(match.start(), match.end()):
                    result.append((tag_name, (), match.start(), match.end()))

        # Find:
        # - "[description](url)" (gray out)
        # - "![description](image_url)" (gray out)
        regexps = (
            (LINK, 'link_color_text'),
            (IMAGE, 'gray_text')
        )
        for regexp, tag_name in regexps:
            for match in re.finditer(regexp, text):
                if not inside_code_blocks(match.start(), match.end()):
                    result.append((tag_name, (),
                                   match.start(), match.start("text")))
                    result.append((tag_name, (),
                                   match.end("text"), match.end()))

        # Find "<url>" links (gray out).
        for match in re.finditer(LINK_ALT, text):
            if not inside_code_blocks(match.start(), match.end()):
                result.append(('gray_text', (), match.start("text"),
                               match.end("text")))

        # Find "---" horizontal rule (center).
        for match in re.finditer(HORIZONTAL_RULE, text):
            if not inside_code_blocks(match.start(), match.end()):
                result.append(('center', (), match.start("symbols"),
                               match.end("symbols")))

        # Find "> blockquote" (offset).
        for match in re.finditer(BLOCK_QUOTE, text):
            if not inside_code_blocks(match.start(), match.end()):
                result.append(('margin_indent', (2, -2),
                               match.start(), match.end()))

        # Find "# Header" (offset+bold).
        for match in re.finditer(HEADER, text):
            if not inside_code_blocks(match.start(), match.end()):
                margin = -len(match.group("level")) - 1
                result.append(('margin_indent', (margin, 0),
                               match.start(), match.end()))
                result.append(('bold', (), match.start(), match.end()))

        # Find "=======" header underline (bold).
        for match in re.finditer(HEADER_UNDER, text):
            if inside_code_blocks(match.start(), match.end()):
                continue
            # check if it's a YAML frontmatter
            frontmatter = re.search(markup_regex.FRONTMATTER, text)
            if frontmatter and match.start() <= frontmatter.end():
                continue
            result.append(('bold', (), match.start(), match.end()))

        child_conn.send((text, result))
