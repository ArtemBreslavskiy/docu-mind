from pydantic import BaseModel
from typing import Literal


class BaseVectorStoreConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class DisabledVectorStoreConfig(BaseVectorStoreConfig):
    type: Literal["disabled"]


class FAISSVectorStoreConfig(BaseVectorStoreConfig):
    type: Literal["faiss"]
