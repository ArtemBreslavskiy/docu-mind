from abc import abstractmethod
from typing import Any
from pydantic import BaseModel
from src.data.db.base import ILanguageExecutor, IHaveSchema


class SQLUpdate(BaseModel):
    match: dict
    update_data: dict


class ISQLReader(ILanguageExecutor, IHaveSchema):
    pass


class ISQLWriter(ILanguageExecutor):
    @abstractmethod
    async def create_one(self, table_name: str, data: dict) -> dict: ...
    @abstractmethod
    async def upsert_one(self, table_name: str, data: dict, conflict_columns: list[str]) -> dict: ...
    @abstractmethod
    async def update_one(self,  table_name: str, update_data: dict, match: dict) -> dict: ...
    @abstractmethod
    async def delete_one(self, table_name: str, match: dict) -> dict: ...
    @abstractmethod
    async def create_many(self, table_name: str, data_list: list[dict]) -> list[Any]: ...
    @abstractmethod
    async def upsert_many(self, table_name: str, data_list: list[dict], conflict_columns: list[str]) -> list[dict]: ...
    @abstractmethod
    async def update_many(self, table_name: str, updates: list[SQLUpdate]) -> list[dict]: ...
    @abstractmethod
    async def update_by_filter(self, table_name: str, update_data: dict, filter: dict) -> list[dict]: ...
    @abstractmethod
    async def delete_many(self, table_name: str, match_list: list[dict]) -> list[dict]: ...
    @abstractmethod
    async def delete_by_filter(self, table_name: str, filter: dict) -> list[dict]: ...
