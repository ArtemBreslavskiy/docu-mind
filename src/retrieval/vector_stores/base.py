from abc import ABC, abstractmethod
from pathlib import Path
from core_schemas import Chunk


class BaseVectorStore(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abstractmethod
    def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        ...

    @abstractmethod
    def search(self, query_embedding: list[float], k: int = 5) -> list[tuple[Chunk, float]]:
        ...

    @abstractmethod
    def list_metadata(self) -> dict[str, list[str]]:
        ...
