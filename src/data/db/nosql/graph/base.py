from abc import abstractmethod
from pydantic import BaseModel
from src.data.db.base import ILanguageExecutor, IHaveSchema


class NodeCreate(BaseModel):
    label: str
    properties: dict


class NodeUpdate(BaseModel):
    match: dict
    update_properties: dict


class RelationshipCreate(BaseModel):
    from_id: str
    to_id: str
    rel_type: str
    properties: dict | None = None


class RelationshipUpdate(BaseModel):
    match: dict
    update_properties: dict


class BaseGraphReader(ILanguageExecutor, IHaveSchema):
    ...


class BaseGraphWriter(ILanguageExecutor):
    @abstractmethod
    async def create_one_node(self, label: str, properties: dict) -> str: ...
    @abstractmethod
    async def upsert_one_node(
        self,
        label: str,
        properties: dict,
        conflict_properties: list[str],
    ) -> str: ...
    @abstractmethod
    async def update_one_node(self, update_properties: dict, match: dict) -> str: ...
    @abstractmethod
    async def delete_one_node(self, match: dict) -> str: ...
    @abstractmethod
    async def create_many_nodes(self, nodes: list[NodeCreate]) -> list[str]: ...
    @abstractmethod
    async def upsert_many_nodes(
        self,
        nodes: list[NodeCreate],
        conflict_properties: list[str],
    ) -> list[str]: ...
    @abstractmethod
    async def update_many_nodes(self, updates: list[NodeUpdate]) -> list[str]: ...
    @abstractmethod
    async def update_many_nodes_by_filter(self, update_properties: dict, filter: dict) -> list[str]: ...
    @abstractmethod
    async def delete_many_nodes(self, match_list: list[dict]) -> list[str]: ...
    @abstractmethod
    async def delete_many_nodes_by_filter(self, filter: dict) -> list[str]: ...
    @abstractmethod
    async def create_one_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: dict | None = None,
    ) -> str: ...
    @abstractmethod
    async def upsert_one_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: dict,
        conflict_properties: list[str],
    ) -> str: ...
    @abstractmethod
    async def update_one_relationship(self, update_properties: dict, match: dict) -> str: ...
    @abstractmethod
    async def delete_one_relationship(self, match: dict) -> str: ...
    @abstractmethod
    async def create_many_relationships(self, rels: list[RelationshipCreate]) -> list[str]: ...
    @abstractmethod
    async def upsert_many_relationships(
        self,
        rels: list[RelationshipCreate],
        conflict_properties: list[str]
    ) -> list[str]: ...
    @abstractmethod
    async def update_many_relationships(self, updates: list[RelationshipUpdate]) -> list[str]: ...
    @abstractmethod
    async def update_many_relationships_by_filter(self, update_properties: dict, filter: dict) -> list[str]: ...
    @abstractmethod
    async def delete_many_relationships(self, match_list: list[dict]) -> list[str]: ...
    @abstractmethod
    async def delete_many_relationships_by_filter(self, filter: dict) -> list[str]: ...

