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
    def list_metadata(self) -> dict[str, list[str]]:
        ...
