import configs.schemas.pipeline.vector.vector_store as vector_stores
import src.configs.schemas.pipeline.embedder as embedders
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
        vector_stores.DisabledVectorStoreConfig,
        vector_stores.FAISSVectorStoreConfig,
    ] = Field(discriminator="type")
    embedder: Union[
        embedders.DisabledEmbedderConfig,
        embedders.SentenceTransformerEmbedderConfig,
    ] = Field(discriminator="type")
