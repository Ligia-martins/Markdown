"""
In-memory representation of a Markdown list.  
Markdown lists are represented as Python lists of ListItem elements.
A ListItem is itself a list of ListItemInnerElem’s.
A ListItemInnerElem is one of: text block (ListItemBlock),
a heading (ListItemHeading),
and, in future versions, a nested MarkdownList (ordered or un-ordered).

----------------------------------------------------------------------
This software is licensed under the MIT License
----------------------------------------------------------------------

Copyright 2022 João Galamba

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
    - The above copyright notice and this permission notice shall be included
      in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""

from abc import ABC, abstractmethod
from typing import Iterable, List

from typing_extensions import override

class MarkdownList(list['ListItem']):
    def __init__(self, iterable: Iterable[ListItem] = ()):
        super().__init__(iterable)
        self.with_paragraphs = False

    def add_new_list_item(self, initial_inner_elem: 'ListItemInnerElem') -> 'ListItem':
        curr_list_item = ListItem()
        curr_list_item.append(initial_inner_elem)
        self.append(curr_list_item)
        return curr_list_item


class ListItem(list['ListItemInnerElem']):
    def add_text_line(self, line: str):
        last_inner_elem = self[-1]

        if isinstance(last_inner_elem, ListItemBlock):
            last_inner_elem.add_line(line)
        elif isinstance(last_inner_elem, ListItemHeading):
            self.append(ListItemBlock(line))
        else:
            assert False, (f"Unknown last item type {type(last_inner_elem)} "
                        f"when adding line: {line}")


class ListItemInnerElem(ABC):
    @abstractmethod
    def __str__(self) -> str:
        pass

    def __repr__(self) -> str:
        return f'{type(self).__name__}: {self}'


class ListItemBlock(ListItemInnerElem):
    def __init__(self, initial_line: str):
        self._text_lines = [initial_line]

    def add_line(self, line: str):
        self._text_lines.append(line)

    @override
    def __str__(self) -> str:
        return '\n'.join(self._text_lines)


class ListItemHeading(ListItemInnerElem):
    def __init__(self, line: str, level: int):
        self._line = line
        self.level = level

    @override
    def __str__(self) -> str:
        return self._line
