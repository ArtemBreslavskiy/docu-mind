import src.configs.schemas.pipeline.sql_reader as reader
import src.configs.schemas.pipeline.sql_writer as writer
from pydantic import BaseModel
from typing import Literal


class BaseSQLDatabaseConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str
    env_key: str
    reader: reader.BaseReaderConfig
    writer: writer.BaseWriterConfig


class DisabledSQLDatabaseConfig(BaseSQLDatabaseConfig):
    type: Literal["disabled"]


class PostgresSQLDatabaseConfig(BaseSQLDatabaseConfig):
    type: Literal["postgres"]
    reader: reader.PostgresReaderConfig
    writer: writer.PostgresWriterConfig
