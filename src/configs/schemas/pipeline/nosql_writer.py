from pydantic import BaseModel
from typing import Literal


class BaseNoSQLWriterConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class DisabledNoSQLWriterConfig(BaseNoSQLWriterConfig):
    type: Literal["disabled"]


class FAISSWriterConfig(BaseNoSQLWriterConfig):
    type: Literal["faiss"]


class Neo4jWriterConfig(BaseNoSQLWriterConfig):
    type: Literal["neo4j"]
    env_key: str
