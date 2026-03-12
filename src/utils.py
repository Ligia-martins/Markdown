"""
Utilitários auxiliares para o compilador Markdown.

Fornece funções de conveniência para:
  - leitura/escrita de ficheiros ou stdin/stdout,
  - manipulação do cursor de leitura de um stream,
  - embelezamento de HTML,
  - correspondência de padrões regex,
  - contagem de caracteres consecutivos.
"""

import re
import sys
from typing import TextIO

from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter

_all__ = [
    'prettify_html', 'from_file_or_stdin', 'to_file_or_stdout',
    'rewind_one_line', 'matches', 'count_consec'
]


def from_file_or_stdin(file_name: str | None) -> TextIO:
    """
    Abre o ficheiro de entrada em modo de leitura de texto (UTF-8).
    Se file_name for None, devolve stdin.
    """
    return open(file_name, 'rt', encoding='UTF-8') if file_name else sys.stdin


def to_file_or_stdout(file_name: str | None) -> TextIO:
    """
    Abre o ficheiro de saída em modo de escrita de texto (UTF-8).
    Se file_name for None, devolve stdout.
    """
    return open(file_name, 'wt', encoding='UTF-8') if file_name else sys.stdout


def rewind_one_line(in_: TextIO, line: str):
    """
    Recua o cursor do stream em exactamente uma linha.

    Útil quando se leu uma linha que pertence ao contexto seguinte
    (por exemplo, ao detectar o fim de uma lista).

    Args:
        in_:  stream de texto posicionado após a linha lida.
        line: a linha que foi lida (sem o '\\n' final, que é reintroduzido
              pelo cálculo do offset em bytes).
    """
    # Calcula o número de bytes da linha mais o newline (\\n) removido
    n_chars = len(line.encode()) + 1
    in_.seek(in_.tell() - n_chars, 0)


def prettify_html(html_code: str | TextIO, indent: int = 2) -> str:
    """
    Recebe HTML em bruto (string ou stream) e devolve-o formatado/indentado
    utilizando o BeautifulSoup.

    Args:
        html_code: código HTML a formatar.
        indent:    número de espaços por nível de indentação (por omissão: 2).

    Returns:
        String com o HTML formatado.
    """
    soup = BeautifulSoup(html_code, features='html.parser')
    return soup.prettify(formatter=HTMLFormatter(indent=indent))


def matches(pattern: re.Pattern, line: str) -> bool:
    """
    Verifica se a linha corresponde integralmente ao padrão regex fornecido
    (equivalente a re.fullmatch, mas devolve um bool em vez de um Match).

    Args:
        pattern: expressão regular compilada.
        line:    linha de texto a testar.

    Returns:
        True se a linha corresponder completamente ao padrão, False caso contrário.
    """
    return bool(pattern.fullmatch(line))


def count_consec(txt: str, char: str, start_pos: int = 0) -> int:
    """
    Conta o número de ocorrências consecutivas de char em txt,
    a partir da posição start_pos.

    Útil para contar os '#' de um cabeçalho Markdown ou os '*' de negrito.

    Args:
        txt:       texto onde procurar.
        char:      caractere a contar (deve ter comprimento 1).
        start_pos: posição inicial na string (por omissão: 0).

    Returns:
        Número de repetições consecutivas de char a partir de start_pos.
    """
    count = 0
    for ch in txt[start_pos:]:
        if ch != char:
            break
        count += 1
    return count
