"""
Representação em memória de uma lista Markdown.

As listas Markdown são representadas como listas Python de elementos ListItem.
Um ListItem é, por sua vez, uma lista de ListItemInnerElem.
Um ListItemInnerElem pode ser:
  - um bloco de texto (ListItemBlock),
  - um cabeçalho (ListItemHeading),
  - futuramente, uma MarkdownList aninhada (ordenada ou não-ordenada).

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
    """
    Representa uma lista Markdown completa (ordenada ou não-ordenada).
    Herda de list para permitir iteração directa sobre os ListItem.

    Atributo:
        with_paragraphs (bool): indica se os blocos de texto dos itens devem
            ser envolvidos em parágrafos. Torna-se True quando existe uma linha
            em branco entre itens da lista.
    """

    def __init__(self, iterable: Iterable['ListItem'] = ()):
        super().__init__(iterable)
        # Flag que indica se os itens da lista contêm parágrafos explícitos
        self.with_paragraphs = False

    def add_new_list_item(self, initial_inner_elem: 'ListItemInnerElem') -> 'ListItem':
        """
        Cria um novo ListItem com o elemento inicial fornecido,
        adiciona-o a esta lista e devolve-o.
        """
        curr_list_item = ListItem()
        curr_list_item.append(initial_inner_elem)
        self.append(curr_list_item)
        return curr_list_item


class ListItem(list['ListItemInnerElem']):
    """
    Representa um único item de lista Markdown.
    É uma lista de ListItemInnerElem (blocos de texto, cabeçalhos, etc.).
    """

    def add_text_line(self, line: str):
        """
        Adiciona uma linha de texto ao último elemento interno deste item.

        - Se o último elemento for um ListItemBlock, a linha é acrescentada a esse bloco.
        - Se for um ListItemHeading, cria-se um novo ListItemBlock para a linha.
        - Qualquer outro tipo lança um AssertionError.
        """
        last_inner_elem = self[-1]

        if isinstance(last_inner_elem, ListItemBlock):
            # Acrescenta a linha ao bloco de texto existente
            last_inner_elem.add_line(line)
        elif isinstance(last_inner_elem, ListItemHeading):
            # Após um cabeçalho, inicia um novo bloco de texto
            self.append(ListItemBlock(line))
        else:
            assert False, (f"Unknown last item type {type(last_inner_elem)} "
                           f"when adding line: {line}")


class ListItemInnerElem(ABC):
    """
    Classe base abstracta para os elementos internos de um item de lista.
    Todas as subclasses devem implementar __str__ para produzir o texto correspondente.
    """

    @abstractmethod
    def __str__(self) -> str:
        pass

    def __repr__(self) -> str:
        """Representação de depuração: mostra o tipo e o conteúdo."""
        return f'{type(self).__name__}: {self}'


class ListItemBlock(ListItemInnerElem):
    """
    Representa um bloco de texto dentro de um item de lista.
    Pode conter várias linhas de texto, que serão unidas com newline.
    """

    def __init__(self, initial_line: str):
        """Inicializa o bloco com a primeira linha de texto."""
        self._text_lines = [initial_line]

    def add_line(self, line: str):
        """Adiciona uma linha adicional ao bloco de texto."""
        self._text_lines.append(line)

    @override
    def __str__(self) -> str:
        """Devolve todas as linhas do bloco unidas por newline."""
        return '\n'.join(self._text_lines)


class ListItemHeading(ListItemInnerElem):
    """
    Representa um cabeçalho embutido dentro de um item de lista.

    Atributos:
        level (int): nível do cabeçalho (1 a 6).
    """

    def __init__(self, line: str, level: int):
        """
        Inicializa o cabeçalho com o texto e o nível.

        Args:
            line:  texto do cabeçalho (sem os marcadores '#').
            level: nível do cabeçalho (número de '#' usados).
        """
        self._line = line
        self.level = level

    @override
    def __str__(self) -> str:
        """Devolve o texto do cabeçalho."""
        return self._line
