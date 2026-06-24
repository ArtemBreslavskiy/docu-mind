from abc import ABC, abstractmethod
from core_schemas import Chunk


class BaseGraphBuilder(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abstractmethod
    def build(self, chunks: list[Chunk], show_progress_bar: bool = True) -> None:
        ...

    @abstractmethod
    def add_documents(self, chunks: list[Chunk], show_progress_bar: bool = True) -> None:
        ...
