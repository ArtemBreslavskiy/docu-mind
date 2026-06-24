import src.configs.schemas.pipeline.chunker as chunker
import src.configs.schemas.pipeline.documents_store as documents_store
from pydantic import BaseModel, Field
from typing import Literal, Union


class BaseDocumentProcessorConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class DisabledDocumentProcessorConfig(BaseDocumentProcessorConfig):
    type: Literal["disabled"]


class DefaultDocumentProcessorConfig(BaseDocumentProcessorConfig):
    type: Literal["default"]
    chunker: Union[
        chunker.DisabledChunkerConfig,
        chunker.RecursiveChunkerConfig
    ] = Field(discriminator="type")
    documents_store: Union[
        documents_store.DisabledDocumentsStoreConfig,
        documents_store.PostgresDocumentsStoreConfig
    ] = Field(discriminator="type")
    loaders: list[Literal["html"]]
