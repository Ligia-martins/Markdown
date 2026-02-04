import sys
from typing import TextIO

from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter

def prettify_html(html_code: str|TextIO, indent = 2) -> str:
    soup = BeautifulSoup(html_code, features='html.parser')
    return soup.prettify(formatter=HTMLFormatter(indent=indent))



def from_file_or_stdin(file_path: str| None) -> TextIO:
    return open(file_path, 'rt') if file_path else sys.stdin


def to_file_or_stdout(file_path: str | None) -> TextIO:
    return open(file_path, 'wt') if file_path else sys.stdout

