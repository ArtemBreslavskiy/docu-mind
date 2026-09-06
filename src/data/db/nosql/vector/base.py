from abc import abstractmethod
from pydantic import BaseModel
from data.db.base import IConnection, ISemanticSearch, IHaveSchema
from src.data.db.filter import FilterCondition, FilterGroup


class VectorAdd(BaseModel):
    vector: list[float]
    metadata: dict


class VectorUpdate(BaseModel):
    match: dict
    update_vector: list[float] | None
    update_metadata: dict | None


class IVectorReader(IConnection, ISemanticSearch, IHaveSchema):
    pass


class IVectorWriter(IConnection):
    @abstractmethod
    async def create_one(self, vector: list[float], metadata: dict) -> str: ...
    @abstractmethod
    async def upsert_one(
        self,
        vector: list[float],
        metadata: dict,
        conflict_properties: list[str],
    ) -> str: ...
    @abstractmethod
    async def update_one(
        self,
        match: dict,
        update_vector: list[float] | None = None,
        update_metadata: dict | None = None,
    ) -> str: ...
    @abstractmethod
    async def delete_one(self, match: dict) -> str: ...
    @abstractmethod
    async def create_many(self, vectors: list[VectorAdd]) -> list[str]: ...
    @abstractmethod
    async def upsert_many(self, vectors: list[VectorAdd], conflict_properties: list[str]) -> list[str]: ...
    @abstractmethod
    async def update_many(self, updates: list[VectorUpdate]) -> list[str]: ...
    @abstractmethod
    async def update_many_by_filter(
        self,
        filter: FilterCondition | FilterGroup,
        update_vector: list[float] | None = None,
        update_metadata: dict | None = None,
    ) -> list[str]: ...
    @abstractmethod
    async def delete_many(self, match_list: list[dict]) -> list[str]: ...
    @abstractmethod
    async def delete_many_by_filter(self, filter: FilterCondition | FilterGroup) -> list[str]: ...
