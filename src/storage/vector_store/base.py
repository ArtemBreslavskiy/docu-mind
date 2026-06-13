from abc import ABC, abstractmethod
from src.core.schemas import Chunk


class BaseVectorStore(ABC):
    @abstractmethod
    def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        ...

    @abstractmethod
    def search(self, query_embedding: list[float], k: int = 5) -> list[tuple[Chunk, float]]:
        ...

    @abstractmethod
    def get_metadata(self, max_examples: int = 30) -> dict[str, list[str]]:
        ...
