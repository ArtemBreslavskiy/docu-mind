from pydantic import BaseModel, Field
from typing import Literal, Union
from abc import ABC, abstractmethod
from src.config.schemas.pipeline.chunker import RecursiveChunkerConfig
from src.config.schemas.pipeline.chunker import BaseChunkerConfig


class BaseDocumentProcessorConfig(BaseModel, ABC):
    model_config = {"extra": "forbid"}

    @property
    @abstractmethod
    def type(self) -> str:
        ...

    @property
    @abstractmethod
    def chunker(self) -> BaseChunkerConfig:
        ...

    @property
    @abstractmethod
    def loaders(self) -> list[Literal["html"]]:
        ...


class DefaultDocumentProcessorConfig(BaseDocumentProcessorConfig):
    type: Literal["default"]
    chunker: Union[RecursiveChunkerConfig] = (Field(discriminator="type"))
    loaders: list[Literal["html"]]
