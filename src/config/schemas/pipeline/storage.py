from pydantic import BaseModel
from typing import Literal


class BaseStorageConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class FAISSStorageConfig(BaseStorageConfig):
    type: Literal["faiss"]
