"""
Ponto de entrada principal do conversor Markos.

Markos é um conversor de Markdown simplificado para HTML.
Aceita input de um ficheiro ou de stdin, e escreve o HTML resultante
para um ficheiro ou para stdout.

Copyright 2026 Hugo Oliveira e Lígia Martins
"""

import sys
from textwrap import dedent
from contextlib import closing

from docopt import docopt

from utils import from_file_or_stdin, to_file_or_stdout
from html_backend import HTMLBackend
from markdown_compiler1 import MarkdownCompiler


def main():
    """
    Função principal do conversor Markos.

    Faz o parsing dos argumentos da linha de comandos com docopt,
    abre os streams de entrada e saída, configura o backend HTML
    e invoca o compilador Markdown.

    Opções da linha de comandos:
      INPUT_FILE   Ficheiro Markdown de entrada (opcional; usa stdin se omitido).
      OUTPUT_FILE  Ficheiro HTML de saída (opcional; usa stdout se omitido).
      -p, --pretty     Formata/indenta o HTML de saída.
      -s STYLE, --style-sheet STYLE  Folha de estilos CSS a incluir no documento HTML.

    Códigos de saída:
      0  Sucesso.
      2  Ficheiro de entrada não encontrado.
      13 Erro de permissões ao aceder a um ficheiro.
    """
    doc = f"""
    Markos is Markdown converter. It converts from Simplified Markdown to HTML.

    Usage:
        {sys.argv[0]} [-s STYLE_SHEET] [-p] [INPUT_FILE] [OUTPUT_FILE]

    Options: 
    -h, --help           Show this help message
    -p, --pretty         Prettify HTML output
    -s STYLE, --style-sheet           Use this STYLE sheet   
    """
    # Faz o parsing dos argumentos usando a docstring acima como especificação
    args = docopt(dedent(doc))
    style_sheet = args['--style-sheet']
    pretty_print = args['--pretty']

    try:
        # Abre o ficheiro de entrada (ou stdin se não fornecido)
        in_file = from_file_or_stdin(args['INPUT_FILE'])
        # Abre o ficheiro de saída (ou stdout se não fornecido)
        out_file = to_file_or_stdout(args['OUTPUT_FILE'])
        # Cria o backend HTML com as opções definidas
        backend = HTMLBackend(out_file, style_sheet, pretty_print)

        # Usa gestores de contexto para garantir o fecho correcto dos recursos
        with in_file, out_file, closing(backend):
            mkd_compiler = MarkdownCompiler(backend)
            mkd_compiler.compile(in_file)

    except FileNotFoundError as ex:
        # Ficheiro de entrada não encontrado
        print(f"File not found: {ex.filename}", file=sys.stderr)
        sys.exit(2)

    except PermissionError as ex:
        # Sem permissões para aceder ao ficheiro
        print(f"Invalid permissions access file: {ex.filename}", file=sys.stderr)
        sys.exit(13)

    except Exception as ex:
        # Qualquer outro erro inesperado: mostra a mensagem e relança a excepção
        print(f"An error has ocurred: \n{ex.args}\n\n", file=sys.stderr)
        raise ex


if __name__ == '__main__':
    main()
