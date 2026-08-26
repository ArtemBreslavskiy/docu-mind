from abc import abstractmethod
from typing import Any
from src.data.db.base import BaseReader, BaseWriter


class BaseCacheReader(BaseReader):
    @abstractmethod
    async def get(self, key: str) -> Any:
        ...

    @abstractmethod
    async def mget(self, keys: list[str]) -> list[Any]:
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        ...

    @abstractmethod
    async def mexists(self, keys: list[str]) -> list[bool]:
        ...

    @abstractmethod
    async def get_ttl(self, key: str) -> int:
        ...

    @abstractmethod
    async def mget_ttl(self, keys: list[str]) -> list[int]:
        ...


class BaseCacheWriter(BaseWriter):
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ...

    @abstractmethod
    async def mset(self, pairs: dict[str, Any]) -> None:
        ...

    @abstractmethod
    async def expire(self, key: str, ttl: int) -> bool:
        ...

    @abstractmethod
    async def expire_at(self, key: str, timestamp: int) -> bool:
        ...

    @abstractmethod
    async def persist(self, key: str) -> bool:
        ...

    @abstractmethod
    async def incr(self, key: str, amount: int = 1) -> int:
        ...

    @abstractmethod
    async def incrbyfloat(self, key: str, amount: float) -> float:
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        ...

    @abstractmethod
    async def mdelete(self, keys: list[str]) -> int:
        ...
