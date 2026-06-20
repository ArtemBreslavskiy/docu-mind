from pydantic import BaseModel, Field
from typing import Literal
from abc import ABC, abstractmethod


class BaseEmbedderConfig(BaseModel, ABC):
    model_config = {"extra": "forbid"}

    @property
    @abstractmethod
    def type(self) -> str:
        ...


class SentenceTransformerEmbedderConfig(BaseEmbedderConfig):
    type: Literal["sentence_transformer"]
    name: str = "BAAI/bge-m3"
    device: str = Field("cuda", pattern=r"^(cpu|cuda(:\d+)?)$")
