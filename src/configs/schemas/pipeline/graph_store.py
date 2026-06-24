from pydantic import BaseModel
from typing import Literal


class BaseGraphStoreConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class DisabledGraphStoreConfig(BaseGraphStoreConfig):
    type: Literal["disabled"]


class Neo4jGraphStoreConfig(BaseGraphStoreConfig):
    type: Literal["neo4j"]
