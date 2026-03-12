"""
Simplified Markdown compiler
"""
from io import StringIO
import re
from enum import Enum
from typing import TextIO

from markdown_backend import MarkdownBackend
from utils import count_consec, matches

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

    BLANK_LINE = re.compile('[ \t\n\r]*')
    HEADING_LINE = re.compile(fr'\s*{INLINE_HEADING_MARKER}{"{1,6}"}(\s+.*)?')
    TEXT_LINE = re.compile(fr'.*\S.*')
    TITLE_LINE = re.compile(fr'{INLINE_TITLE_MARKER}.*\S.*{INLINE_TITLE_MARKER}')

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

        for line in in_:
            line = line[:-1]
            
            if state is CompilerState.OUTSIDE and  matches(self.HEADING_LINE, line):
                self._new_heading(line)

            elif state is CompilerState.OUTSIDE and matches(self.TEXT_LINE, line):
                backend.open_par()
                backend.new_par_line(line)
                state = CompilerState.INSIDE_PAR

            elif state is CompilerState.INSIDE_PAR and matches(self.BLANK_LINE, line):
                backend.close_par()
                state = CompilerState.OUTSIDE

            elif state is CompilerState.INSIDE_PAR and matches(self.HEADING_LINE, line):
                backend.close_par()
                self._new_heading(line)
                state = CompilerState.OUTSIDE

            elif state is CompilerState.INSIDE_PAR and matches(self.TEXT_LINE, line):
                backend.new_par_line(line)

            else:
                assert state is CompilerState.OUTSIDE and matches(self.BLANK_LINE, line), f'Unknow line \"{line}\" for state {state}'

        backend.close_document()

    def _new_heading(self, line_with_markers: str):
        backend = self._backend
        text, level = self._parse_heading(line_with_markers)
        backend.open_heading(level)
        backend.new_text_line(text)
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