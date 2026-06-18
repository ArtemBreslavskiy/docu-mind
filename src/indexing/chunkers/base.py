from abc import ABC, abstractmethod
from core_schemas import Chunk, Document


class BaseChunker(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abstractmethod
    def split(self, documents: list[Document]) -> list[Chunk]:
        ...
