"""
Define a interface abstracta (classe base) para todos os backends do compilador Markdown.

Um "backend" é responsável por gerar o formato de saída final (por exemplo, HTML).
Qualquer backend concreto deve herdar desta classe e implementar todos os métodos abstractos.
"""

from abc import ABC, abstractmethod


class MarkdownBackend(ABC):
    """
    Classe base abstracta que define o contrato que todos os backends devem cumprir.
    Cada método corresponde a uma operação de geração de conteúdo (abrir/fechar elementos,
    escrever texto inline, etc.).
    """

    @abstractmethod
    def open_document(self, title=''):
        """Abre o documento de saída, opcionalmente com um título."""
        pass

    @abstractmethod
    def close_document(self):
        """Fecha o documento de saída (escreve marcadores de fecho, se necessário)."""
        pass

    @abstractmethod
    def open_heading(self, level: int):
        """Abre um cabeçalho do nível especificado (1 a 6)."""
        pass

    @abstractmethod
    def close_heading(self, level: int):
        """Fecha um cabeçalho do nível especificado."""
        pass

    @abstractmethod
    def new_text_line(self, line: str):
        """Emite uma nova linha de texto simples."""
        pass

    @abstractmethod
    def open_par(self):
        """Abre um parágrafo."""
        pass

    @abstractmethod
    def close_par(self):
        """Fecha um parágrafo."""
        pass

    @abstractmethod
    def new_par_line(self, line: str):
        """Emite uma linha de texto dentro de um parágrafo já aberto."""
        pass

    @abstractmethod
    def open_list(self):
        """Abre uma lista não-ordenada."""
        pass

    @abstractmethod
    def close_list(self):
        """Fecha uma lista não-ordenada."""
        pass

    @abstractmethod
    def open_list_item(self):
        """Abre um item de lista."""
        pass

    @abstractmethod
    def close_list_item(self):
        """Fecha um item de lista."""
        pass

    # --- Elementos inline ---

    @abstractmethod
    def inline_bold(self, text: str):
        """Emite texto em negrito."""
        pass

    @abstractmethod
    def inline_italic(self, text: str):
        """Emite texto em itálico."""
        pass

    @abstractmethod
    def inline_link(self, text: str, url: str, title: str = ''):
        """Emite uma hiperligação com texto, URL e título opcionais."""
        pass

    @abstractmethod
    def inline_image(self, alt: str, url: str, title: str = ''):
        """Emite uma imagem com texto alternativo, URL e título opcionais."""
        pass

    @abstractmethod
    def inline_text(self, text: str):
        """Emite texto simples sem formatação especial."""
        pass

    # --- Listas ordenadas ---

    @abstractmethod
    def open_ordered_list(self):
        """Abre uma lista ordenada (numerada)."""
        pass

    @abstractmethod
    def close_ordered_list(self):
        """Fecha uma lista ordenada."""
        pass
