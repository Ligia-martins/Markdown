from typing import TextIO

__all__= ['MarkdownCompiler', 'CompilationError']

class CompilationError(Exception):
    """
    A generic compilation error. This could be due to invalid Markdown or some other problem
    """

class MarkdownCompiler:
    """
    Implements a Simplified Markdown parser and compiler. Please refer to the 'compile' method documentation.
    """
    def __init__ (self, backend):
        self.backend = backend

    def compile(self, in_: TextIO ):
        self.backend.document('Um título qualquer')
