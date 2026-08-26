from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    ...


class SearchTextCallable(ABC):
    @abstractmethod
    async def search_text(self, table: str, field: str, query: str, limit: int = 10) -> list[dict]:
        ...


class SearchSemanticCallable(ABC):
    @abstractmethod
    async def search_semantic(self, table: str, field: str, query: str, limit: int = 10) -> list[dict]:
        ...


class GetDistinctValuesCallable(ABC):
    @abstractmethod
    async def get_distinct_values(self, table: str, field: str, limit: int = 20) -> list[Any]:
        ...


class CountRecordsCallable(ABC):
    @abstractmethod
    async def count_records(self, table: str, filter: dict | None = None) -> int:
        ...


class ReadQueryExecutor(ABC):
    @abstractmethod
    async def execute_read_query(self, query: Any, params: dict | None = None) -> list[dict]:
        ...


class WriteQueryExecutor(ABC):
    @abstractmethod
    async def execute_write_query(self, query: Any, params: dict | None = None) -> int:
        ...


class GetSchemaInfoCallable(ABC):
    @abstractmethod
    async def get_schema_info(self) -> dict:
        ...
