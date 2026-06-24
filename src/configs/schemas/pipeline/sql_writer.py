from pydantic import BaseModel


class BaseWriterConfig(BaseModel):
    enable: bool = False


class PostgresWriterConfig(BaseWriterConfig):
    enable: bool = False
