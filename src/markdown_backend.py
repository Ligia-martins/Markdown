"""
Docstring for backend
"""

from abc import ABC, abstractmethod


class MarkdownBackend(ABC):
    @abstractmethod
    def open_document(self, title=''):
        pass

    @abstractmethod
    def close_document(self):
        pass

    @abstractmethod
    def open_heading(self, level:int):
        pass

    @abstractmethod
    def close_heading(self, level:int):
        pass

    @abstractmethod
    def new_text_line(self, line: str):
        pass

    @abstractmethod
    def open_par(self):
        pass

    @abstractmethod
    def close_par(self):
        pass

    @abstractmethod
    def new_par_line(self, line: str):
        pass

    @abstractmethod
    def open_list(self):
        pass
    
    @abstractmethod
    def close_list(self):
        pass

    @abstractmethod
    def open_list_item(self):
        pass
    
    @abstractmethod
    def close_list_item(self):
        pass

###INLINE###
    @abstractmethod
    def inline_bold(self, text: str):
        pass

    @abstractmethod
    def inline_italic(self, text: str):
        pass

    @abstractmethod
    def inline_link(self, text: str, url: str, title: str = ''):
        pass

    @abstractmethod
    def inline_image(self, alt: str, url: str, title: str = ''):
        pass

    @abstractmethod
    def inline_text(self, text: str):
        pass

###ORDERD LISTS###
    @abstractmethod
    def open_ordered_list(self):
        pass

    @abstractmethod
    def close_ordered_list(self):
        pass