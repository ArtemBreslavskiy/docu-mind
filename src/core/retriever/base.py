from abc import ABC, abstractmethod
from src.core.schemas import SearchResult


class BaseRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, k: 5) -> list[SearchResult]:
        ...

    @abstractmethod
    def retrieve_with_filter(
        self,
        query: str,
        filter_key: str | None = None,
        filter_value: str | None = None,
        filter_json: str | None = None,
        k: int = 5
    ) -> list[SearchResult]:
        ...
