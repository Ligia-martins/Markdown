import re
import sys
from typing import TextIO

from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter

_all__ = ['prettify_html', 'from_file_or_stdin', 'to_file_or_stdout', 'rewind_one_line', 'matches', 'count_consec']


def from_file_or_stdin(file_name: str | None) -> TextIO:
    return open(file_name, 'rt', encoding='UTF-8') if file_name else sys.stdin
    

def to_file_or_stdout(file_name: str | None) -> TextIO:
    return open(file_name, 'wt', encoding='UTF-8') if file_name else sys.stdout

def rewind_one_line(in_: TextIO, line: str):
    n_chars = len(line.encode()) + 1  # '+1' accounts for the removed '\n\r'
    in_.seek(in_.tell() - n_chars, 0)
    
def prettify_html(html_code: str | TextIO, indent = 2) -> str:
    soup = BeautifulSoup(html_code, features='html.parser')
    return soup.prettify(formatter=HTMLFormatter(indent = indent))

def matches(pattern: re.Pattern, line: str) -> bool:
    return bool(pattern.fullmatch(line))

def count_consec(txt: str, char:str, start_pos: int=0):
    count = 0
    for ch in txt[start_pos:]:
        if ch != char:
            break
        count += 1
    return count

