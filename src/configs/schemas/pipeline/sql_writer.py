from pydantic import BaseModel
from typing import Literal


class BaseSQLWriterConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class DisabledSQLWriterConfig(BaseSQLWriterConfig):
    type: Literal["disabled"]


class PostgresWriterConfig(BaseSQLWriterConfig):
    type: Literal["postgres"]
    env_key: str
    name: str
    description: str
