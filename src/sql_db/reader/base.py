from abc import ABC, abstractmethod
from typing import Any


class BaseSQLReader(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @abstractmethod
    async def select(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_schema_info(self) -> dict[str, Any]:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...
