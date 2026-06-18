from pydantic import BaseModel, Field
from typing import Literal
from abc import ABC, abstractmethod


class BaseChunkerConfig(BaseModel, ABC):
    model_config = {"extra": "forbid"}

    @property
    @abstractmethod
    def type(self) -> str:
        ...


class RecursiveChunkerConfig(BaseChunkerConfig):
    type: Literal["recursive"] = "recursive"
    chunk_size: int = Field(512, ge=128, le=4096)
    chunk_overlap: int = Field(64, ge=0, le=1024)
    separators: list[str] = ["\n\n", "\n", ". ", " ", ""]
