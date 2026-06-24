from abc import ABC, abstractmethod
from typing import Any


class BaseSQLWriter(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @abstractmethod
    async def insert_one(self, table: str, data: dict[str, Any]) -> Any:
        ...

    @abstractmethod
    async def update_one(self, table: str, filter: dict[str, Any], update_data: dict[str, Any]) -> int:
        ...

    @abstractmethod
    async def delete_one(self, table: str, filter: dict[str, Any]) -> int:
        ...

    @abstractmethod
    async def insert_many(self, table: str, data_list: list[dict[str, Any]]) -> int:
        ...

    @abstractmethod
    async def update_many(self, table: str, filter: dict[str, Any], update_data: dict[str, Any]) -> int:
        ...

    @abstractmethod
    async def delete_many(self, table: str, filter: dict[str, Any]) -> int:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...
