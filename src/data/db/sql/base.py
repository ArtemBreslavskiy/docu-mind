from abc import abstractmethod, ABC
from typing import Any
from pydantic import BaseModel
from src.data.db.base import BaseReader, BaseWriter


class SQLUpdate(BaseModel):
    match: dict[str, Any]
    update_data: dict[str, Any]


class BaseSQLReader(BaseReader):
    ...


class BaseSQLWriter(ABC, BaseWriter):
    @abstractmethod
    async def create_one(self, table_name: str, data: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    async def upsert_one(self, table_name: str, data: dict[str, Any], conflict_columns: list[str]) -> dict[str, Any]:
        ...

    @abstractmethod
    async def update_one(self,  table_name: str, update_data: dict[str, Any], match: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    async def delete_one(self, table_name: str, match: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    async def create_many(self, table_name: str, data_list: list[dict[str, Any]]) -> list[Any]:
        ...

    @abstractmethod
    async def upsert_many(
        self,
        table_name: str,
        data_list: list[dict[str, Any]],
        conflict_columns: list[str],
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def update_many(self, table_name: str, updates: list[SQLUpdate]) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def update_by_filter(
        self,
        table_name: str,
        update_data: dict[str, Any],
        filter: dict[str, Any]
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def delete_many(self, table_name: str, match_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def delete_by_filter(self, table_name: str, filter: dict[str, Any]) -> list[dict[str, Any]]:
        ...
