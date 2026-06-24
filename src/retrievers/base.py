from abc import ABC, abstractmethod
from core_schemas import SearchResult


class BaseRetriever(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abstractmethod
    def retrieve(self, query: str, k: int = 5) -> list[SearchResult]:
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
