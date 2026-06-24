from pydantic import BaseModel


class BaseReaderConfig(BaseModel):
    enable: bool = True


class PostgresReaderConfig(BaseReaderConfig):
    enable: bool = True
