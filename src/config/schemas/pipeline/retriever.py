from pydantic import BaseModel, Field
from typing import Literal
from abc import ABC, abstractmethod


class BaseRetrieverConfig(BaseModel, ABC):
    model_config = {"extra": "forbid"}

    @property
    @abstractmethod
    def type(self) -> str:
        ...


class DenseRetrieverConfig(BaseRetrieverConfig):
    type: Literal["dense"]
    filter_oversample_factor: int = Field(
        4, ge=2, le=10,
        description="Multiplier for initial retrieval count before filtering"
    )
