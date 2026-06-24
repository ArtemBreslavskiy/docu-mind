from abc import ABC, abstractmethod
from typing import Any


class BaseNoSQLWriter(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @abstractmethod
    async def insert_one(self, collection: str, document: dict[str, Any]) -> str:
        ...

    @abstractmethod
    async def insert_many(self, collection: str, documents: list[dict[str, Any]]) -> list[str]:
        ...

    @abstractmethod
    async def update_one(
        self,
        collection: str,
        filter: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> int:
        ...

    @abstractmethod
    async def update_many(
        self,
        collection: str,
        filter: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> int:
        ...

    @abstractmethod
    async def delete_one(self, collection: str, filter: dict[str, Any]) -> int:
        ...

    @abstractmethod
    async def delete_many(self, collection: str, filter: dict[str, Any]) -> int:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...
