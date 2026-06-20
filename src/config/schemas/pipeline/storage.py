from pydantic import BaseModel
from typing import Literal
from abc import ABC, abstractmethod


class BaseStorageConfig(BaseModel, ABC):
    model_config = {"extra": "forbid"}

    @property
    @abstractmethod
    def type(self) -> str:
        ...


class FAISSStorageConfig(BaseStorageConfig):
    type: Literal["faiss"]
