"""
Backend HTML para o compilador Markdown.

Implementa MarkdownBackend produzindo HTML como saída.
O HTML é primeiro acumulado num StringIO interno e, no momento do fecho,
escrito no destino final (ficheiro ou stdout), opcionalmente formatado/indentado.
"""

from io import StringIO
import re
from typing import TextIO
from typing_extensions import override

from markdown_backend import MarkdownBackend
from utils import prettify_html

__all__ = ['HTMLBackend']


class HTMLBackend(MarkdownBackend):
    """
    Backend concreto que gera HTML a partir das chamadas do compilador Markdown.

    O conteúdo HTML é acumulado num buffer interno (StringIO) durante a compilação.
    Ao fechar o backend, o buffer é escrito no destino final, com formatação
    opcional se pretty_print=True.

    Args:
        out:          stream de saída (ficheiro ou stdout).
        style_sheet:  caminho/URL para uma folha de estilos CSS (opcional).
        pretty_print: se True, o HTML de saída é indentado/formatado.
    """

    def __init__(self, out: TextIO, style_sheet: str = '', pretty_print: bool = False):
        self._storage = out          # destino final de escrita
        self._out = StringIO()       # buffer onde o HTML é construído
        self._style_sheet = style_sheet
        self._pretty_print = pretty_print

    def close(self):
        """
        Escreve o conteúdo do buffer no destino final.
        Se pretty_print estiver activo, formata o HTML antes de escrever.
        """
        content = self._out.getvalue()
        self._storage.write(prettify_html(content) if self._pretty_print else content)
        self._out.close()

    # --- Documento ---

    @override
    def open_document(self, title: str = ''):
        """
        Emite o cabeçalho HTML do documento (<DOCTYPE>, <html>, <head>).
        Inclui o <title> se fornecido e o <link> para a folha de estilos, se definida.
        Nota: existe um bug na linha do <link> (falta o '>'), mas mantém-se o comportamento original.
        """
        out = self._out
        # Estrutura base do documento HTML5 (newlines removidas para compacidade)
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
            # ATENÇÃO: falta fechar a tag com '>' — bug no código original
            out.write(f'<link rel="stylesheet media="all" type="text/css" src="{self._style_sheet}"')
        out.write('</head><body>')

    @override
    def close_document(self):
        """Fecha as tags <body> e <html>."""
        self._out.write('</body></html>')

    # --- Cabeçalhos ---

    @override
    def open_heading(self, level: int):
        """Emite a tag de abertura do cabeçalho (ex: <h1>, <h2>, ...)."""
        self._out.write(f'<h{level}>')

    @override
    def close_heading(self, level: int):
        """Emite a tag de fecho do cabeçalho (ex: </h1>, </h2>, ...)."""
        self._out.write(f'</h{level}>')

    # --- Parágrafos ---

    @override
    def open_par(self):
        """Emite a tag de abertura de parágrafo <p>."""
        self._out.write(f'<p>')

    @override
    def close_par(self):
        """Emite a tag de fecho de parágrafo </p>."""
        self._out.write(f'</p>')

    # --- Listas não-ordenadas ---

    @override
    def open_list(self):
        """Emite a tag de abertura de lista não-ordenada <ul>."""
        self._out.write(f'<ul>')

    @override
    def close_list(self):
        """Emite a tag de fecho de lista não-ordenada </ul>."""
        self._out.write(f'</ul>')

    @override
    def open_list_item(self):
        """Emite a tag de abertura de item de lista <li>."""
        self._out.write(f'<li>')

    @override
    def close_list_item(self):
        """Emite a tag de fecho de item de lista </li>."""
        self._out.write(f'</li>')

    # --- Elementos inline ---

    @override
    def inline_text(self, text: str):
        """Emite texto simples sem qualquer marcação adicional."""
        self._out.write(text)

    @override
    def inline_bold(self, text: str):
        """Emite texto em negrito usando a tag <strong>."""
        self._out.write(f'<strong>{text}</strong>')

    @override
    def inline_italic(self, text: str):
        """Emite texto em itálico usando a tag <em>."""
        self._out.write(f'<em>{text}</em>')

    @override
    def inline_link(self, text: str, url: str, title: str = ''):
        """
        Emite uma hiperligação HTML (<a>).

        Args:
            text:  texto visível da ligação.
            url:   endereço de destino.
            title: texto de tooltip (atributo title).
        """
        self._out.write(f'<a href="{url}" title="{title}">{text}</a>')

    @override
    def inline_image(self, alt: str, url: str, title: str = ''):
        """
        Emite uma imagem HTML (<img>).

        Args:
            alt:   texto alternativo (atributo alt).
            url:   caminho/URL da imagem.
            title: texto de tooltip (atributo title).
        """
        self._out.write(f'<img src="{url}" alt="{alt}" title="{title}">')

    @override
    def new_text_line(self, line: str):
        """Emite uma linha de texto simples (sem formatação de parágrafo)."""
        self._out.write(line)

    @override
    def new_par_line(self, line: str):
        """
        Emite uma linha de continuação dentro de um parágrafo.
        Adiciona um espaço antes da linha para separar do texto anterior.
        """
        self._out.write(f' {line}')

    # --- Listas ordenadas ---

    @override
    def open_ordered_list(self):
        """Emite a tag de abertura de lista ordenada <ol>."""
        self._out.write('<ol>')

    @override
    def close_ordered_list(self):
        """Emite a tag de fecho de lista ordenada </ol>."""
        self._out.write('</ol>')
