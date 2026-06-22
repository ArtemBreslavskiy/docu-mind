from pydantic import BaseModel, Field
from typing import Literal, Union
from src.config.schemas.pipeline.chunker import RecursiveChunkerConfig
from src.config.schemas.pipeline.documents_store import PostgresDocumentsStoreConfig


class BaseDocumentProcessorConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class DefaultDocumentProcessorConfig(BaseDocumentProcessorConfig):
    type: Literal["default"]
    chunker: Union[RecursiveChunkerConfig] = (Field(discriminator="type"))
    documents_store: Union[PostgresDocumentsStoreConfig] = (Field(discriminator="type"))
    loaders: list[Literal["html"]]
