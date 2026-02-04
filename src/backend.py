from abc import ABC, abstractmethod
from typing import TextIO
from io import StringIO
from typing_extensions import override

from utils import prettify_html

#ABC=> Abstract Base Class

class MarkdownBackend(ABC):
    @abstractmethod
    def open_document(self, title = ''):
        pass

    @abstractmethod
    def close_document(self, title = ''):
        pass

    @abstractmethod
    def open_heading(self, level = int):
        pass

    @abstractmethod
    def close_heading(self, level = int):
        pass



class HTMLBackend(MarkdownBackend):
    def __init__(self, out:TextIO, style_sheet = '', pretty_print = False):
        self._storage = out
        self._out = StringIO()
        self._style_sheet = style_sheet
        self._pretty_print = pretty_print

    def close(self):
        self.close_document()
        self._storage.write(
            prettify_html(self._out.getvalue()) if self._pretty_print else 
                            self._out.getvalue()
    )
        self._out.close()

    @override
    def open_document(self, title=''):
        out= self._out
        out.write (""" 
<!DOCTYPE html>
<html lang = "en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="Viewport" content ="width=device-width, initial-scale=1.0">
""".replace('\n', ''))
        if title:
            out.write(f'<title>{title}</title>')
        if self._style_sheet:
            out.write('<link rel="stylesheet" media = "all" type = "text/css"'
                      f'src="{self._style_sheet}"')
        out.write('</head><body>')

@override
def close_document(self):
    self._out.write('</body></html>')
        