from abc import ABC, abstractmethod
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from pydantic import BaseModel
from src.core.chunkers.base import Chunk


class IConnection(ABC):
    @abstractmethod
    async def connect(self) -> None: ...
    @abstractmethod
    async def close(self) -> None: ...
    @abstractmethod
    async def ping(self) -> bool: ...


class ITransactional(ABC):
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[None, None]:
        await self.begin_transaction()
        try:
            yield
            await self.commit_transaction()
        except Exception:
            await self.rollback_transaction()
            raise

    @abstractmethod
    async def begin_transaction(self) -> None: ...
    @abstractmethod
    async def commit_transaction(self) -> None: ...
    @abstractmethod
    async def rollback_transaction(self) -> None: ...


class ILanguageExecutor(ABC):
    @abstractmethod
    async def execute(self, query: str, params: dict | None = None) -> list[dict]: ...


class IHaveSchema(ABC):
    @abstractmethod
    async def get_schema_info(self) -> str: ...


class SemanticSearchResult(BaseModel):
    id: str
    chunk: Chunk
    score: float


class ISemanticSearch(ABC):
    @abstractmethod
    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter: dict | None = None
    ) -> list[SemanticSearchResult]:
        ...
