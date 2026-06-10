from abc import ABC, abstractmethod
from src.core.schemas import Chunk


class BaseVectorStore(ABC):
    @abstractmethod
    def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        ...

    def search(self, query_embedding: list[float], k: int = 5) -> list[tuple[Chunk, float]]:
        ...
