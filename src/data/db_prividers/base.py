from abc import ABC, abstractmethod
from typing import Any


class BaseDBProvider(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abstractmethod
    def get_description(self) -> list[str]:
        ...

    @abstractmethod
    async def get_source_info(self, source_name: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def execute_query(
        self,
        source_name: str,
        query: Any,
        params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def search_text(
        self,
        source_name: str,
        table_or_collection: str,
        field: str,
        query: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_distinct_values(
        self,
        source_name: str,
        table_or_collection: str,
        field: str,
        limit: int = 20
    ) -> list[Any]:
        ...

    @abstractmethod
    async def count_records(
        self,
        source_name: str,
        table_or_collection: str,
        filter: dict[str, Any] | None = None
    ) -> int:
        ...

    @abstractmethod
    async def get_schema(self, source_name: str) -> dict[str, Any]:
        ...
