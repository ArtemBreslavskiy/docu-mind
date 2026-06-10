from abc import ABC, abstractmethod
from src.core.schemas import SearchResult


class BaseRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, k: 5) -> list[SearchResult]:
        ...
