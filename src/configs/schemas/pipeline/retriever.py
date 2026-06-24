import src.configs.schemas.pipeline.vector_store as vector_store
import configs.schemas.pipeline.embedder as embedder
from pydantic import BaseModel, Field
from typing import Literal, Union


class BaseRetrieverConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class DisabledRetrieverConfig(BaseRetrieverConfig):
    type: Literal["disabled"]


class DenseRetrieverConfig(BaseRetrieverConfig):
    type: Literal["dense"]
    filter_oversample_factor: int = Field(4, ge=2, le=10)
    vector_store: Union[
        vector_store.DisabledVectorStoreConfig,
        vector_store.FAISSVectorStoreConfig,
    ] = Field(discriminator="type")
    embedder: Union[
        embedder.DisabledEmbedderConfig,
        embedder.SentenceTransformerEmbedderConfig,
    ] = Field(discriminator="type")
