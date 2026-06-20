from pydantic import BaseModel, Field
from typing import Literal, Union
from abc import ABC, abstractmethod
from src.config.schemas.pipeline.storage import FAISSStorageConfig
from config.schemas.pipeline.embedder import SentenceTransformerEmbedderConfig


class BaseRetrieverConfig(BaseModel, ABC):
    model_config = {"extra": "forbid"}

    @property
    @abstractmethod
    def type(self) -> str:
        ...


class DenseRetrieverConfig(BaseRetrieverConfig):
    type: Literal["dense"]
    vector_storage: Union[FAISSStorageConfig] = (Field(discriminator="type"))
    embedder: Union[SentenceTransformerEmbedderConfig] = Field(discriminator="type")
    filter_oversample_factor: int = Field(
        4, ge=2, le=10,
        description="Multiplier for initial retrieval count before filtering"
    )
