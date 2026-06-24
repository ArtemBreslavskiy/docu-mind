from abc import ABC, abstractmethod
from typing import Any


class BaseNoSQLReader(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @abstractmethod
    async def find(
        self,
        collection: str,
        filter: dict[str, Any],
        projection: dict[str, Any] | None = None,
        sort: list[tuple] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def find_one(
        self,
        collection: str,
        filter: dict[str, Any],
        projection: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        ...

    @abstractmethod
    async def get_collections(self) -> list[str]:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...
