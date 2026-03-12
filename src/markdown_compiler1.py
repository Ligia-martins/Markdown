"""
Simplified Markdown compiler
"""
from functools import singledispatchmethod
from io import StringIO
import re
from enum import Enum
from typing import TextIO

from markdown_backend import MarkdownBackend
from markdown_list import(MarkdownList, ListItem, ListItemInnerElem, ListItemBlock, ListItemHeading)
from utils import count_consec, matches, rewind_one_line

__all__ = ['MarkdownCompiler', 'CompilationError']

class CompilationError(Exception):
    """
    A generic compilation error. This could be invalid Markdown
    or some other problem.
    """

class MarkdownCompiler:
    """
    Implements a Simplified Markdown parser and compiler. Please refer to
    the 'compile' method documentation.
    """

    INLINE_TITLE_MARKER = '!'
    INLINE_HEADING_MARKER = '#'
    INLINE_ULIST_MARKER = '-'

    BLANK_LINE = re.compile('[ \t\n\r]*')
    
    UNINDENT_HEADING_LINE = re.compile(fr'\s?{INLINE_HEADING_MARKER}{"{1,6}"}(\s+.*)?')
    INDENT_HEADING_LINE = re.compile(fr'\s{"{2,}"}{INLINE_HEADING_MARKER}{"{1,6}"}(\s+.*)?')

    UNINDENT_TEXT_LINE = re.compile(r'\s?\S.*')
    INDENT_TEXT_LINE = re.compile(r'\s{2,}\S.*')

    # LIST_ITEM_LINE = re.compile(fr'\s{"{,3}"}{INLINE_ULIST_MARKER}(\s+.*)?')
    LIST_ITEM_LINE = re.compile(r'\s{,3}[-*](\s+.*)?')
    TITLE_LINE = re.compile(fr'{INLINE_TITLE_MARKER}.*\S.*{INLINE_TITLE_MARKER}')
    
###INLINE###
    INLINE = re.compile(
        r'(?P<image>!\[(?P<img_alt>[^\]]*)\]\((?P<img_url>[^\s\)"]*)\s*(?:"(?P<img_title>[^"]*)")?\))'
        r'|(?P<link>\[(?P<link_text>[^\]]*)\]\((?P<link_url>[^\s\)"]*)\s*(?:"(?P<link_title>[^"]*)")?\))'
        r'|(?P<bold>\*\*(.+?)\*\*|__(.+?)__)'
        r'|(?P<italic>\*(.+?)\*|_(.+?)_)'
    )

###ORDERED LIST###
    ORDERED_LIST_ITEM_LINE = re.compile(r'\s{,3}\d+[.)]\s+.*')


    def __init__(self, backend: MarkdownBackend):
        self._backend = backend

    # MAIN STATE MACHINE

    def compile(self, in_:TextIO |  str):

        if isinstance(in_, str):
            in_ = StringIO(in_)
            
        backend = self._backend
        title = self._read_title(in_)
        self._backend.open_document(title)

        CompilerState = Enum('CompilerState', 'OUTSIDE INSIDE_PAR NEW_LIST')
        state = CompilerState.OUTSIDE

        while line := in_.readline():  
            line = line[:-1]
                        
            if state is CompilerState.OUTSIDE and self._is_heading_line(line):
                self._new_heading(line)

            elif state is CompilerState.OUTSIDE and matches(self.LIST_ITEM_LINE, line):
                rewind_one_line(in_, line) 
                self._compile_list(in_)
                state = CompilerState.NEW_LIST

            elif state is CompilerState.OUTSIDE and matches(self.ORDERED_LIST_ITEM_LINE, line):
                rewind_one_line(in_, line)
                self._compile_list(in_, ordered=True)
                state = CompilerState.NEW_LIST

            elif state is CompilerState.OUTSIDE and self._is_text_line(line):
                backend.open_par()
                # backend.new_par_line(line)
                self._compile_inline(line)  
                state = CompilerState.INSIDE_PAR

            elif state is CompilerState.INSIDE_PAR and matches(self.BLANK_LINE, line):
                backend.close_par()
                state = CompilerState.OUTSIDE

            elif state is CompilerState.INSIDE_PAR and self._is_heading_line(line):
                backend.close_par()
                self._new_heading(line)
                state = CompilerState.OUTSIDE

            elif state is CompilerState.INSIDE_PAR and matches(self.LIST_ITEM_LINE, line):
                backend.close_par()
                rewind_one_line(in_, line) 
                self._compile_list(in_)
                state = CompilerState.NEW_LIST

            elif state is CompilerState.INSIDE_PAR and matches(self.ORDERED_LIST_ITEM_LINE, line):
                rewind_one_line(in_, line)
                self._compile_list(in_, ordered=True)
                state = CompilerState.NEW_LIST

            elif state is CompilerState.INSIDE_PAR and self._is_text_line(line):
                # backend.new_par_line(line)
                self._compile_inline(line)

            elif state is CompilerState.NEW_LIST and matches(self.UNINDENT_HEADING_LINE, line):
                self._new_heading(line)
                state = CompilerState.OUTSIDE

            elif state is CompilerState.NEW_LIST and matches(self.UNINDENT_TEXT_LINE, line):
                backend.open_par()
                # backend.new_par_line(line)
                self._compile_inline(line)
                state = CompilerState.INSIDE_PAR

            else:
                assert state is CompilerState.OUTSIDE and matches(self.BLANK_LINE, line), f"Unknow line \"{line}\" for state {state}"

        backend.close_document()


    def _new_heading(self, line_with_markers: str):
        backend = self._backend
        text, level = self._parse_heading(line_with_markers)
        backend.open_heading(level)
        # backend.new_text_line(text)
        self._compile_inline(text)  
        backend.close_heading(level)

    def _parse_heading(self, line_with_markers: str) -> tuple[str, int]:
        line_with_markers = line_with_markers.lstrip()
        count = count_consec(line_with_markers, self.INLINE_HEADING_MARKER)
        assert count>0, 'No heading markers found'
        text = line_with_markers[count:].strip()
        return text, count

    def _read_title(self, in_: TextIO) -> str:
        first_line = in_.readline()[:-1]
        second_line = in_.readline()
        if matches(self.TITLE_LINE, first_line) and matches(self.BLANK_LINE, second_line):
            return first_line[1:-1].strip()
        in_.seek(0)
        return ''
    
    def _is_heading_line(self, line:str) -> bool:
        return matches(self.UNINDENT_HEADING_LINE, line) or matches(self.INDENT_HEADING_LINE, line)
    
    def _is_text_line(self, line:str) -> bool:
        return matches(self.UNINDENT_TEXT_LINE, line) or matches(self.INDENT_TEXT_LINE, line)
    

    def _compile_list(self, in_: TextIO, ordered: bool = False):
        """
        LIST GENERATION STATE MACHINE

        The following code implements a State Machine (SM) just for list processing. Handling lists is tricky because:

            • List items can have embedded elements inside, like paragraphs, headers and nested lists (NOTE: nested lists are not implemented in this project)

            • If a list item has a paragraph, even if it's the last one, then all text blocks inside the other list items should be wrapped in paragraphs.

            • Indented and unindented elements have different meanings when inside a list item. An unindented header will close the list element, while an indented one will be part of the list item. The same applies to the first line of new paragraphs.

        - Unlike with a regular paragraph, a blank line doesn't always end the list. A blank line may end the list if it's followed by an unindented text line. But if the following text line is indented, then the current list item continues, now with a new nested paragraph.

        - Because we don't know for sure how to generate code for list items without reading all items first, this SM stores each list item in data structure (similar to Python list). The entire list rendered only after the end of the list is reached.

        - The first line in the input stream should be the line with the initial list item. The SM ends when an unrecognized line is read. When this happens, the line that caused the SM to stop is put back onto the stream (the stream is rewound by one line).
        """
        line = in_.readline()[:-1]
        assert matches(self.LIST_ITEM_LINE, line) or matches(self.ORDERED_LIST_ITEM_LINE, line), f'First line not a list item |{line}|'
        
        mkd_list = MarkdownList()
        curr_list_item = mkd_list.add_new_list_item(
            self._new_list_item_inner_elem(line)
        )

        ListState = Enum('ListState', 'LIST_ITEM MAY_END')
        state = ListState.LIST_ITEM

        while line:= in_.readline():
            line = line[:-1]

            if matches(self.UNINDENT_HEADING_LINE, line):
                # End of list: rewind the reader and terminate de SM.
                # An unindented heading terminates the list regardless of the current state.
                rewind_one_line(in_, line)
                break
            
            elif state is ListState.LIST_ITEM and matches(self.LIST_ITEM_LINE, line):
                curr_list_item = mkd_list.add_new_list_item(
                    self._new_list_item_inner_elem(line)
                )
            
            elif state is ListState.LIST_ITEM and matches(self.ORDERED_LIST_ITEM_LINE, line):
                curr_list_item = mkd_list.add_new_list_item(
                    self._new_list_item_inner_elem(line)
                )
            
            elif state is ListState.LIST_ITEM and matches(self.INDENT_HEADING_LINE, line):
                curr_list_item.append(self._new_list_item_heading(line))
            
            elif state is ListState.LIST_ITEM and self._is_text_line(line):
                curr_list_item.add_text_line(line)

            elif state is ListState.LIST_ITEM and matches(self.BLANK_LINE, line):
                state = ListState.MAY_END

            elif state is ListState.MAY_END and matches(self.LIST_ITEM_LINE, line):
                curr_list_item = mkd_list.add_new_list_item(
                    self._new_list_item_inner_elem(line)
                )
                mkd_list.with_paragraphs = True
                state = ListState.LIST_ITEM

            elif state is ListState.MAY_END and matches(self.ORDERED_LIST_ITEM_LINE, line):
                curr_list_item = mkd_list.add_new_list_item(
                    self._new_list_item_inner_elem(line)
                )
                mkd_list.with_paragraphs = True
                state = ListState.LIST_ITEM

            elif state is ListState.MAY_END and matches(self.INDENT_HEADING_LINE, line):
                curr_list_item.append(self._new_list_item_heading(line))
                mkd_list.with_paragraphs = True
                state = ListState.LIST_ITEM

            elif state is ListState.MAY_END and matches(self.INDENT_TEXT_LINE, line):
                curr_list_item.append(ListItemBlock(line))
                mkd_list.with_paragraphs = True
                state = ListState.LIST_ITEM

            elif state is ListState.MAY_END and matches(self.UNINDENT_TEXT_LINE, line):
                # End of list: rewind the TextIO and terminate de SM.
                rewind_one_line(in_, line)
                break

            else:
                assert state is ListState.MAY_END and matches(self.BLANK_LINE, line), \
                    f"Unknow line \"{line}\" for state {state}"

        self._compile_markdown_list(mkd_list, ordered)
        # self.__dumpMarkdownList(mkd_list)

        

    # def _new_list_item_inner_elem(self, initial_line: str) -> ListItemInnerElem:
    #     line = initial_line.strip()[1:] #remove list marker
    #     if self._is_heading_line(line):
    #         return self._new_list_item_heading(line)
    #     return ListItemBlock(line)

    def _new_list_item_inner_elem(self, initial_line: str) -> ListItemInnerElem:
        line = initial_line.strip()
        # remover o marcador: '-' para não-ordenada, '1.' ou '1)' para ordenada
        if line[0] in (self.INLINE_ULIST_MARKER, '*'):
            line = line[1:]  # remove só o '-'
        else:
            line = re.sub(r'^\d+[.)]', '', line)  # remove '1.' ou '1)'
        line = line.strip()
        if self._is_heading_line(line):
            return self._new_list_item_heading(line)
        return ListItemBlock(line)
        
    def _new_list_item_heading(self, line_with_markers: str) -> ListItemHeading:
        line, level = self._parse_heading(line_with_markers)
        return ListItemHeading(line, level)


    # def _compile_markdown_list(self, mkd_list: MarkdownList):
    #     backend = self._backend
    #     backend.open_list()
    #     for list_item in mkd_list:
    #         self._compile_list_item(list_item, mkd_list.with_paragraphs)
    #     backend.close_list()
        

    def _compile_markdown_list(self, mkd_list: MarkdownList, ordered: bool = False):
        backend = self._backend
        if ordered:
            backend.open_ordered_list()
        else:
            backend.open_list()
        for list_item in mkd_list:
            self._compile_list_item(list_item, mkd_list.with_paragraphs)
        if ordered:
            backend.close_ordered_list()
        else:
            backend.close_list()

    def _compile_list_item(self, list_item: ListItem, with_paragraphs: bool):
        backend = self._backend
        backend.open_list_item()
        for inner_elem in list_item:
            self._compile_list_item_inner_elem(inner_elem, with_paragraphs)
        backend.close_list_item()
    
    @singledispatchmethod
    def _compile_list_item_inner_elem(self, elem, *_, **__):
        raise NotImplemented(f"Unknown inner elem '{elem}' of type {type(elem)}")

    @_compile_list_item_inner_elem.register # type: ignore
    def _(self, block: ListItemBlock, with_paragraphs: bool):
        backend = self._backend
        if with_paragraphs:
            backend.open_par()
            # backend.new_par_line(str(block))
            self._compile_inline(str(block))
            backend.close_par()
        else:
            # backend.new_par_line(str(block))
            self._compile_inline(str(block))

    @_compile_list_item_inner_elem.register # type: ignore
    def _(self, heading: ListItemHeading, *_):
        backend = self._backend
        backend.open_heading(heading.level)
        # backend.new_text_line(str(heading))
        self._compile_inline(str(heading))
        backend.close_heading(heading.level)

    def __dump_markdown_list(self, mkd_list: MarkdownList):
        print("MARKDOWN LIST")
        for list_item in mkd_list:
            print("LIST ITEM")
            for inner_elem in list_item:
                print(repr(inner_elem))

###INLINE###
    def _compile_inline(self, text: str):
        backend = self._backend
        last_end = 0

        for match in self.INLINE.finditer(text):
            # texto normal antes do elemento inline
            if match.start() > last_end:
                backend.inline_text(text[last_end:match.start()])

            if match.group('image'):
                backend.inline_image(
                    alt   = match.group('img_alt') or '',
                    url   = match.group('img_url') or '',
                    title = match.group('img_title') or ''
                )
            elif match.group('link'):
                backend.inline_link(
                    text  = match.group('link_text') or '',
                    url   = match.group('link_url') or '',
                    title = match.group('link_title') or ''
                )
            
            elif match.group('bold'):
                # group(10) é o texto do ** e group(11) é o texto do __
                txt = next(g for g in match.groups()[9:11] if g is not None)
                backend.inline_bold(txt)

            elif match.group('italic'):
                # group(13) é o texto do * e group(14) é o texto do _
                txt = next(g for g in match.groups()[12:14] if g is not None)
                backend.inline_italic(txt)


            last_end = match.end()

        # texto normal restante
        if last_end < len(text):
            backend.inline_text(text[last_end:])
