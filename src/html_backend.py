

from io import StringIO
import re
from typing import TextIO
from typing_extensions import override

from markdown_backend import MarkdownBackend
from utils import prettify_html

__all__= ['HTMLBackend']


class HTMLBackend(MarkdownBackend):
    def __init__(self, out:TextIO, style_sheet='', pretty_print = False):
        self._storage = out
        self._out = StringIO()
        self._style_sheet = style_sheet
        self._pretty_print = pretty_print

    def close(self):
        self._storage.write(prettify_html(self._out.getvalue()) if self._pretty_print else self._out.getvalue())
        self._out.close()

    @override
    def open_document(self, title=''):
        out = self._out
        self._out.write("""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            """.replace('\n', ''))
        if title:
            out.write(f'<title>{title}</title>')
        if self._style_sheet:
            out.write(f'<link rel="stylesheet media="all" type="text/css" src="{self._style_sheet}"')
        out.write('</head><body>')

    @override
    def close_document(self):
        self._out.write('</body></html>')

    @override
    def open_heading(self, level:int):
        self._out.write(f'<h{level}>')

    @override
    def close_heading(self, level:int):
        self._out.write(f'</h{level}>')

    # @override
    # def new_text_line(self, line: str):
    #     self._out.write(line)

    @override
    def open_par(self):
        self._out.write(f'<p>')

    @override
    def close_par(self):
        self._out.write(f'</p>')

    # @override
    # def new_par_line(self, line: str):
    #     self._out.write(f' {line}')

    @override
    def open_list(self):
        self._out.write(f'<ul>')
    
    @override
    def close_list(self):
        self._out.write(f'</ul>')

    @override
    def open_list_item(self):
        self._out.write(f'<li>')
    
    @override
    def close_list_item(self):
        self._out.write(f'</li>')

###INLINE###
    @override
    def inline_text(self, text: str):
        self._out.write(text)

    @override
    def inline_bold(self, text: str):
        self._out.write(f'<strong>{text}</strong>')

    @override
    def inline_italic(self, text: str):
        self._out.write(f'<em>{text}</em>')

    @override
    def inline_link(self, text: str, url: str, title: str = ''):
        self._out.write(f'<a href="{url}" title="{title}">{text}</a>')

    @override
    def inline_image(self, alt: str, url: str, title: str = ''):
        self._out.write(f'<img src="{url}" alt="{alt}" title="{title}">')

    @override
    def new_text_line(self, line: str):
        self._out.write(line)  # por agora deixa assim, o compiler vai tratar os inline

    @override
    def new_par_line(self, line: str):
        self._out.write(f' {line}')  # idem

###ORDERED LIST###
    @override
    def open_ordered_list(self):
        self._out.write('<ol>')

    @override
    def close_ordered_list(self):
        self._out.write('</ol>')








