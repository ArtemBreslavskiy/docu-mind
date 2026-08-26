from abc import ABC, abstractmethod
from src.core.schemas import SearchResult


class BaseRetriever(ABC):
    @abstractmethod
    async def search(self, query: str, k: int = 5) -> list[SearchResult]:
        ...
