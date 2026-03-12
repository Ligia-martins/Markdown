"""
Compilador Markdown simplificado.

Implementa um parser/compilador de Markdown simplificado usando uma máquina de estados.
Suporta: títulos de documento, cabeçalhos, parágrafos, listas ordenadas e não-ordenadas,
e elementos inline (negrito, itálico, hiperligações, imagens).
"""

from functools import singledispatchmethod
from io import StringIO
import re
from enum import Enum
from typing import TextIO

from markdown_backend import MarkdownBackend
from markdown_list import (MarkdownList, ListItem, ListItemInnerElem, ListItemBlock, ListItemHeading)
from utils import count_consec, matches, rewind_one_line

__all__ = ['MarkdownCompiler', 'CompilationError']


class CompilationError(Exception):
    """
    Erro genérico de compilação. Pode indicar Markdown inválido
    ou qualquer outro problema durante o processo de compilação.
    """


class MarkdownCompiler:
    """
    Implementa um parser e compilador de Markdown simplificado.
    Consultar a documentação do método 'compile' para mais detalhes.
    """

    # Marcadores inline reconhecidos pelo compilador
    INLINE_TITLE_MARKER = '!'       # Delimitador de título de documento (!Título!)
    INLINE_HEADING_MARKER = '#'     # Marcador de cabeçalho (#, ##, ...)
    INLINE_ULIST_MARKER = '-'       # Marcador de lista não-ordenada (-)

    # Linha em branco: apenas espaços, tabs ou newlines
    BLANK_LINE = re.compile('[ \t\n\r]*')

    # Cabeçalho não-indentado: começa com espaço opcional + 1-6 '#'
    UNINDENT_HEADING_LINE = re.compile(fr'\s?{INLINE_HEADING_MARKER}{"{1,6}"}(\s+.*)?')
    # Cabeçalho indentado: começa com 2+ espaços + 1-6 '#'
    INDENT_HEADING_LINE = re.compile(fr'\s{"{2,}"}{INLINE_HEADING_MARKER}{"{1,6}"}(\s+.*)?')

    # Linha de texto não-indentada: começa com espaço opcional + pelo menos um caractere não-espaço
    UNINDENT_TEXT_LINE = re.compile(r'\s?\S.*')
    # Linha de texto indentada: começa com 2+ espaços + caractere não-espaço
    INDENT_TEXT_LINE = re.compile(r'\s{2,}\S.*')

    # Item de lista não-ordenada: até 3 espaços + '-' ou '*' + conteúdo opcional
    LIST_ITEM_LINE = re.compile(r'\s{,3}[-*](\s+.*)?')
    # Linha de título do documento: começa e acaba com '!'
    TITLE_LINE = re.compile(fr'{INLINE_TITLE_MARKER}.*\S.*{INLINE_TITLE_MARKER}')

    # --- Padrão para elementos inline ---
    # Reconhece imagens, hiperligações, negrito e itálico (por esta ordem de prioridade)
    INLINE = re.compile(
        r'(?P<image>!\[(?P<img_alt>[^\]]*)\]\((?P<img_url>[^\s\)"]*)\s*(?:"(?P<img_title>[^"]*)")?\))'
        r'|(?P<link>\[(?P<link_text>[^\]]*)\]\((?P<link_url>[^\s\)"]*)\s*(?:"(?P<link_title>[^"]*)")?\))'
        r'|(?P<bold>\*\*(.+?)\*\*|__(.+?)__)'
        r'|(?P<italic>\*(.+?)\*|_(.+?)_)'
    )

    # Item de lista ordenada: até 3 espaços + dígitos + '.' ou ')' + espaço + conteúdo
    ORDERED_LIST_ITEM_LINE = re.compile(r'\s{,3}\d+[.)]\s+.*')

    def __init__(self, backend: MarkdownBackend):
        """
        Inicializa o compilador com o backend de saída fornecido.

        Args:
            backend: instância de MarkdownBackend que receberá os eventos de compilação.
        """
        self._backend = backend

    # =========================================================================
    # MÁQUINA DE ESTADOS PRINCIPAL
    # =========================================================================

    def compile(self, in_: TextIO | str):
        """
        Compila o Markdown lido a partir de 'in_' usando uma máquina de estados.

        A máquina tem três estados:
          - OUTSIDE:    fora de qualquer bloco (parágrafo ou lista).
          - INSIDE_PAR: dentro de um parágrafo activo.
          - NEW_LIST:   imediatamente após o fecho de uma lista.

        Cada linha lida é classificada por tipo e, dependendo do estado actual,
        provoca uma transição e/ou uma acção sobre o backend.

        Args:
            in_: stream de texto ou string com o conteúdo Markdown a compilar.
        """
        if isinstance(in_, str):
            in_ = StringIO(in_)

        backend = self._backend
        title = self._read_title(in_)        # lê o título opcional do documento
        self._backend.open_document(title)

        CompilerState = Enum('CompilerState', 'OUTSIDE INSIDE_PAR NEW_LIST')
        state = CompilerState.OUTSIDE

        while line := in_.readline():
            line = line[:-1]  # remove o '\n' final

            # --- Estado OUTSIDE ---

            if state is CompilerState.OUTSIDE and self._is_heading_line(line):
                # Linha de cabeçalho: processa directamente
                self._new_heading(line)

            elif state is CompilerState.OUTSIDE and matches(self.LIST_ITEM_LINE, line):
                # Início de lista não-ordenada: devolve a linha ao stream e delega
                rewind_one_line(in_, line)
                self._compile_list(in_)
                state = CompilerState.NEW_LIST

            elif state is CompilerState.OUTSIDE and matches(self.ORDERED_LIST_ITEM_LINE, line):
                # Início de lista ordenada: devolve a linha ao stream e delega
                rewind_one_line(in_, line)
                self._compile_list(in_, ordered=True)
                state = CompilerState.NEW_LIST

            elif state is CompilerState.OUTSIDE and self._is_text_line(line):
                # Início de parágrafo
                backend.open_par()
                self._compile_inline(line)
                state = CompilerState.INSIDE_PAR

            # --- Estado INSIDE_PAR ---

            elif state is CompilerState.INSIDE_PAR and matches(self.BLANK_LINE, line):
                # Linha em branco fecha o parágrafo
                backend.close_par()
                state = CompilerState.OUTSIDE

            elif state is CompilerState.INSIDE_PAR and self._is_heading_line(line):
                # Cabeçalho dentro de parágrafo: fecha o parágrafo e processa o cabeçalho
                backend.close_par()
                self._new_heading(line)
                state = CompilerState.OUTSIDE

            elif state is CompilerState.INSIDE_PAR and matches(self.LIST_ITEM_LINE, line):
                # Lista não-ordenada dentro de parágrafo: fecha o parágrafo e delega
                backend.close_par()
                rewind_one_line(in_, line)
                self._compile_list(in_)
                state = CompilerState.NEW_LIST

            elif state is CompilerState.INSIDE_PAR and matches(self.ORDERED_LIST_ITEM_LINE, line):
                # Lista ordenada dentro de parágrafo: fecha o parágrafo e delega
                rewind_one_line(in_, line)
                self._compile_list(in_, ordered=True)
                state = CompilerState.NEW_LIST

            elif state is CompilerState.INSIDE_PAR and self._is_text_line(line):
                # Linha de continuação do parágrafo actual
                self._compile_inline(line)

            # --- Estado NEW_LIST ---

            elif state is CompilerState.NEW_LIST and matches(self.UNINDENT_HEADING_LINE, line):
                # Cabeçalho após lista
                self._new_heading(line)
                state = CompilerState.OUTSIDE

            elif state is CompilerState.NEW_LIST and matches(self.UNINDENT_TEXT_LINE, line):
                # Texto após lista: inicia novo parágrafo
                backend.open_par()
                self._compile_inline(line)
                state = CompilerState.INSIDE_PAR

            else:
                # Apenas linha em branco no estado OUTSIDE é válida aqui
                assert state is CompilerState.OUTSIDE and matches(self.BLANK_LINE, line), \
                    f"Unknow line \"{line}\" for state {state}"

        backend.close_document()

    # =========================================================================
    # CABEÇALHOS
    # =========================================================================

    def _new_heading(self, line_with_markers: str):
        """
        Processa uma linha de cabeçalho: determina o nível, emite a abertura,
        compila o conteúdo inline e emite o fecho.
        """
        backend = self._backend
        text, level = self._parse_heading(line_with_markers)
        backend.open_heading(level)
        self._compile_inline(text)
        backend.close_heading(level)

    def _parse_heading(self, line_with_markers: str) -> tuple[str, int]:
        """
        Extrai o texto e o nível de um cabeçalho Markdown.

        Remove o espaço inicial, conta os '#' consecutivos e devolve
        o texto restante (sem os marcadores) e o nível (1 a 6).

        Returns:
            Tuplo (texto_do_cabeçalho, nível).
        """
        line_with_markers = line_with_markers.lstrip()
        count = count_consec(line_with_markers, self.INLINE_HEADING_MARKER)
        assert count > 0, 'No heading markers found'
        text = line_with_markers[count:].strip()
        return text, count

    def _read_title(self, in_: TextIO) -> str:
        """
        Tenta ler o título do documento a partir das primeiras linhas do stream.

        O título é reconhecido se a primeira linha corresponder ao padrão TITLE_LINE
        (!Título!) e a segunda linha for em branco. Se não houver título, o stream
        é reposicionado no início.

        Returns:
            O texto do título (sem os '!') ou string vazia se não existir título.
        """
        first_line = in_.readline()[:-1]
        second_line = in_.readline()
        if matches(self.TITLE_LINE, first_line) and matches(self.BLANK_LINE, second_line):
            return first_line[1:-1].strip()  # remove os '!' delimitadores
        in_.seek(0)
        return ''

    def _is_heading_line(self, line: str) -> bool:
        """Devolve True se a linha for um cabeçalho (indentado ou não-indentado)."""
        return matches(self.UNINDENT_HEADING_LINE, line) or matches(self.INDENT_HEADING_LINE, line)

    def _is_text_line(self, line: str) -> bool:
        """Devolve True se a linha for uma linha de texto (indentada ou não-indentada)."""
        return matches(self.UNINDENT_TEXT_LINE, line) or matches(self.INDENT_TEXT_LINE, line)

    # =========================================================================
    # MÁQUINA DE ESTADOS PARA LISTAS
    # =========================================================================

    def _compile_list(self, in_: TextIO, ordered: bool = False):
        """
        Máquina de estados para processamento de listas Markdown.

        Complexidades tratadas por esta máquina:
          - Itens de lista podem conter parágrafos, cabeçalhos e listas aninhadas
            (listas aninhadas ainda não implementadas).
          - Se um item tiver parágrafo, todos os blocos de texto são envolvidos
            em parágrafos (with_paragraphs=True).
          - Elementos indentados pertencem ao item actual; os não-indentados encerram a lista.
          - Uma linha em branco pode encerrar a lista (se seguida de texto não-indentado)
            ou continuar o item actual (se seguida de texto indentado).
          - Como não se sabe a priori se há parágrafos, os itens são primeiro acumulados
            numa estrutura MarkdownList e só depois compilados para o backend.
          - A primeira linha do stream deve ser o primeiro item da lista.
          - Quando a máquina termina, a linha que provocou a paragem é devolvida ao stream.

        Args:
            in_:     stream de texto posicionado na primeira linha do item de lista.
            ordered: se True, gera uma lista ordenada (<ol>); caso contrário, não-ordenada (<ul>).
        """
        line = in_.readline()[:-1]
        assert matches(self.LIST_ITEM_LINE, line) or matches(self.ORDERED_LIST_ITEM_LINE, line), \
            f'First line not a list item |{line}|'

        mkd_list = MarkdownList()
        # Cria o primeiro item da lista com o conteúdo da primeira linha
        curr_list_item = mkd_list.add_new_list_item(
            self._new_list_item_inner_elem(line)
        )

        ListState = Enum('ListState', 'LIST_ITEM MAY_END')
        state = ListState.LIST_ITEM

        while line := in_.readline():
            line = line[:-1]

            # Cabeçalho não-indentado: encerra sempre a lista
            if matches(self.UNINDENT_HEADING_LINE, line):
                rewind_one_line(in_, line)
                break

            # --- Estado LIST_ITEM: dentro de um item de lista activo ---

            elif state is ListState.LIST_ITEM and matches(self.LIST_ITEM_LINE, line):
                # Novo item de lista não-ordenada
                curr_list_item = mkd_list.add_new_list_item(
                    self._new_list_item_inner_elem(line)
                )

            elif state is ListState.LIST_ITEM and matches(self.ORDERED_LIST_ITEM_LINE, line):
                # Novo item de lista ordenada
                curr_list_item = mkd_list.add_new_list_item(
                    self._new_list_item_inner_elem(line)
                )

            elif state is ListState.LIST_ITEM and matches(self.INDENT_HEADING_LINE, line):
                # Cabeçalho indentado: pertence ao item actual
                curr_list_item.append(self._new_list_item_heading(line))

            elif state is ListState.LIST_ITEM and self._is_text_line(line):
                # Linha de texto: acrescenta ao último bloco do item actual
                curr_list_item.add_text_line(line)

            elif state is ListState.LIST_ITEM and matches(self.BLANK_LINE, line):
                # Linha em branco: a lista pode ou não terminar aqui (depende da linha seguinte)
                state = ListState.MAY_END

            # --- Estado MAY_END: linha em branco foi encontrada; aguardar próxima linha ---

            elif state is ListState.MAY_END and matches(self.LIST_ITEM_LINE, line):
                # Novo item após linha em branco: a lista continua; activa with_paragraphs
                curr_list_item = mkd_list.add_new_list_item(
                    self._new_list_item_inner_elem(line)
                )
                mkd_list.with_paragraphs = True
                state = ListState.LIST_ITEM

            elif state is ListState.MAY_END and matches(self.ORDERED_LIST_ITEM_LINE, line):
                curr_list_item = mkd_list.add_new_list_item(
                    self._new_list_item_inner_elem(line)
                )
                mkd_list.with_paragraphs = True
                state = ListState.LIST_ITEM

            elif state is ListState.MAY_END and matches(self.INDENT_HEADING_LINE, line):
                # Cabeçalho indentado após linha em branco: pertence ao item actual
                curr_list_item.append(self._new_list_item_heading(line))
                mkd_list.with_paragraphs = True
                state = ListState.LIST_ITEM

            elif state is ListState.MAY_END and matches(self.INDENT_TEXT_LINE, line):
                # Texto indentado após linha em branco: novo bloco no item actual
                curr_list_item.append(ListItemBlock(line))
                mkd_list.with_paragraphs = True
                state = ListState.LIST_ITEM

            elif state is ListState.MAY_END and matches(self.UNINDENT_TEXT_LINE, line):
                # Texto não-indentado após linha em branco: a lista terminou
                rewind_one_line(in_, line)
                break

            else:
                # Única situação válida restante: segunda linha em branco consecutiva no estado MAY_END
                assert state is ListState.MAY_END and matches(self.BLANK_LINE, line), \
                    f"Unknow line \"{line}\" for state {state}"

        # Compila a lista acumulada para o backend
        self._compile_markdown_list(mkd_list, ordered)

    def _new_list_item_inner_elem(self, initial_line: str) -> ListItemInnerElem:
        """
        Cria o elemento interno inicial de um item de lista a partir da sua primeira linha.

        Remove o marcador de lista ('-', '*' para não-ordenada; '1.' ou '1)' para ordenada)
        e determina se o conteúdo restante é um cabeçalho ou um bloco de texto simples.

        Args:
            initial_line: linha do item de lista (com o marcador).

        Returns:
            ListItemHeading se o conteúdo for um cabeçalho; ListItemBlock caso contrário.
        """
        line = initial_line.strip()
        # Remove o marcador de lista
        if line[0] in (self.INLINE_ULIST_MARKER, '*'):
            line = line[1:]                        # remove '-' ou '*'
        else:
            line = re.sub(r'^\d+[.)]', '', line)   # remove '1.' ou '1)'
        line = line.strip()
        if self._is_heading_line(line):
            return self._new_list_item_heading(line)
        return ListItemBlock(line)

    def _new_list_item_heading(self, line_with_markers: str) -> ListItemHeading:
        """
        Cria um ListItemHeading a partir de uma linha de cabeçalho (com os '#').

        Returns:
            ListItemHeading com o texto e o nível do cabeçalho.
        """
        line, level = self._parse_heading(line_with_markers)
        return ListItemHeading(line, level)

    def _compile_markdown_list(self, mkd_list: MarkdownList, ordered: bool = False):
        """
        Compila uma MarkdownList completa para o backend.

        Abre a lista (ordenada ou não), compila cada item e fecha a lista.

        Args:
            mkd_list: lista acumulada com todos os itens.
            ordered:  se True, usa open/close_ordered_list; caso contrário, open/close_list.
        """
        backend = self._backend
        if ordered:
            backend.open_ordered_list()
        else:
            backend.open_list()
        for list_item in mkd_list:
            self._compile_list_item(list_item, mkd_list.with_paragraphs)
        if ordered:
            backend.close_ordered_list()
        else:
            backend.close_list()

    def _compile_list_item(self, list_item: ListItem, with_paragraphs: bool):
        """
        Compila um único item de lista para o backend.

        Abre o item, compila cada elemento interno e fecha o item.

        Args:
            list_item:      item a compilar.
            with_paragraphs: se True, os blocos de texto serão envolvidos em <p>.
        """
        backend = self._backend
        backend.open_list_item()
        for inner_elem in list_item:
            self._compile_list_item_inner_elem(inner_elem, with_paragraphs)
        backend.close_list_item()

    @singledispatchmethod
    def _compile_list_item_inner_elem(self, elem, *_, **__):
        """
        Despacha a compilação de um elemento interno de item de lista.
        Lança NotImplemented para tipos desconhecidos.
        """
        raise NotImplemented(f"Unknown inner elem '{elem}' of type {type(elem)}")

    @_compile_list_item_inner_elem.register  # type: ignore
    def _(self, block: ListItemBlock, with_paragraphs: bool):
        """
        Compila um bloco de texto de item de lista.

        Se with_paragraphs for True, envolve o texto em <p>; caso contrário,
        emite o texto directamente.
        """
        backend = self._backend
        if with_paragraphs:
            backend.open_par()
            self._compile_inline(str(block))
            backend.close_par()
        else:
            self._compile_inline(str(block))

    @_compile_list_item_inner_elem.register  # type: ignore
    def _(self, heading: ListItemHeading, *_):
        """
        Compila um cabeçalho embutido num item de lista.
        """
        backend = self._backend
        backend.open_heading(heading.level)
        self._compile_inline(str(heading))
        backend.close_heading(heading.level)

    def __dump_markdown_list(self, mkd_list: MarkdownList):
        """Método de depuração: imprime a estrutura interna da lista."""
        print("MARKDOWN LIST")
        for list_item in mkd_list:
            print("LIST ITEM")
            for inner_elem in list_item:
                print(repr(inner_elem))

    # =========================================================================
    # ELEMENTOS INLINE
    # =========================================================================

    def _compile_inline(self, text: str):
        """
        Processa os elementos inline de uma linha de texto e envia-os para o backend.

        Itera sobre todas as correspondências do padrão INLINE no texto.
        Entre correspondências, o texto simples é emitido via inline_text.
        Cada correspondência é despachada para o método inline adequado do backend
        (imagem, hiperligação, negrito, itálico).

        Args:
            text: linha de texto com possíveis elementos inline.
        """
        backend = self._backend
        last_end = 0  # posição do fim da última correspondência processada

        for match in self.INLINE.finditer(text):
            # Emite o texto simples antes desta correspondência, se existir
            if match.start() > last_end:
                backend.inline_text(text[last_end:match.start()])

            if match.group('image'):
                # Imagem: ![alt](url "título")
                backend.inline_image(
                    alt=match.group('img_alt') or '',
                    url=match.group('img_url') or '',
                    title=match.group('img_title') or ''
                )
            elif match.group('link'):
                # Hiperligação: [texto](url "título")
                backend.inline_link(
                    text=match.group('link_text') or '',
                    url=match.group('link_url') or '',
                    title=match.group('link_title') or ''
                )
            elif match.group('bold'):
                # Negrito: **texto** ou __texto__
                # O grupo 10 corresponde a ** e o grupo 11 a __
                txt = next(g for g in match.groups()[9:11] if g is not None)
                backend.inline_bold(txt)
            elif match.group('italic'):
                # Itálico: *texto* ou _texto_
                # O grupo 13 corresponde a * e o grupo 14 a _
                txt = next(g for g in match.groups()[12:14] if g is not None)
                backend.inline_italic(txt)

            last_end = match.end()

        # Emite o texto simples restante após a última correspondência
        if last_end < len(text):
            backend.inline_text(text[last_end:])
