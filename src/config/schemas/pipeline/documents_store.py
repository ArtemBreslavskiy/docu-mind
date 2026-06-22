from pydantic import BaseModel
from typing import Literal


class BaseDocumentsStoreConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class PostgresDocumentsStoreConfig(BaseDocumentsStoreConfig):
    type: Literal["postgres"]
