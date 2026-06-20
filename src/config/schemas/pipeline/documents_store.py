from pydantic import BaseModel
from typing import Literal
from abc import ABC, abstractmethod


class BaseDocumentsStoreConfig(BaseModel, ABC):
    model_config = {"extra": "forbid"}

    @property
    @abstractmethod
    def type(self) -> str:
        ...


class PostgresDocumentsStoreConfig(BaseDocumentsStoreConfig):
    type: Literal["postgres"]
