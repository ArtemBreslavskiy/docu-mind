from pydantic import BaseModel
from typing import Literal


class BaseNoSQLReaderConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class DisabledNoSQLReaderConfig(BaseNoSQLReaderConfig):
    type: Literal["disabled"]


class FAISSReaderConfig(BaseNoSQLReaderConfig):
    type: Literal["faiss"]


class Neo4jReaderConfig(BaseNoSQLReaderConfig):
    type: Literal["neo4j"]
    env_key: str
