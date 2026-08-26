from pydantic import BaseModel
from typing import Literal


class BaseSQLReaderConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class DisabledSQLReaderConfig(BaseSQLReaderConfig):
    type: Literal["disabled"]


class PostgresReaderConfig(BaseSQLReaderConfig):
    type: Literal["postgres"]
    env_key: str
    name: str
    description: str
