from abc import abstractmethod
from typing import Any
from pydantic import BaseModel
from data.db.base import BaseReader, BaseWriter
from src.core.chunkers.base import Chunk


class VectorSearchResult(BaseModel):
    id: str
    chunk: Chunk
    score: float


class VectorAdd(BaseModel):
    id: str | None
    vector: list[float]
    metadata: dict[str, Any]


class VectorUpdate(BaseModel):
    id: str
    vector: list[float] | None
    metadata: dict[str, Any] | None


class BaseVectorReader(BaseReader):
    @abstractmethod
    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None
    ) -> list[VectorSearchResult]:
        ...


class BaseVectorWriter(BaseWriter):
    @abstractmethod
    async def create_one(
        self,
        vector: list[float],
        metadata: dict[str, Any],
        vector_id: str | None = None
    ) -> str:
        ...

    @abstractmethod
    async def update_one(
        self,
        vector_id: str,
        vector: list[float] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> None:
        ...

    @abstractmethod
    async def delete_one(self, vector_id: str) -> None:
        ...

    @abstractmethod
    async def create_many(self, vectors: list[VectorAdd]) -> list[str]:
        ...

    @abstractmethod
    async def update_many(self, updates: list[VectorUpdate]) -> None:
        ...

    @abstractmethod
    async def delete_many(self, vector_ids: list[str]) -> None:
        ...
