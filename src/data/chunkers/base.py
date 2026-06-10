from abc import ABC, abstractmethod
from src.core.schemas import Chunk, Document


class BaseChunker(ABC):
    @abstractmethod
    def split(self, documents: list[Document]) -> list[Chunk]:
        ...
