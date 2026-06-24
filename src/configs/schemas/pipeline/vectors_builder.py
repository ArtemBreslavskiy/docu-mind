import src.configs.schemas.pipeline.embedder as embedder
import src.configs.schemas.pipeline.vector_store as vector_store
from pydantic import BaseModel, Field
from typing import Literal, Union


class BaseVectorsBuilderConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class DisabledVectorsBuilderConfig(BaseVectorsBuilderConfig):
    type: Literal["disabled"]


class DefaultVectorsBuilderConfig(BaseVectorsBuilderConfig):
    type: Literal["default"]
    vector_store: Union[
        vector_store.DisabledVectorStoreConfig,
        vector_store.FAISSVectorStoreConfig,
    ] = Field(discriminator="type")
    embedder: Union[
        embedder.DisabledEmbedderConfig,
        embedder.SentenceTransformerEmbedderConfig,
    ] = Field(discriminator="type")
