from abc import ABC, abstractmethod
from src.core_schemas import Chunk


class BaseVectorsBuilder(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abstractmethod
    def build(self, chunks: list[Chunk], show_progress_bar: bool = True) -> None:
        ...
