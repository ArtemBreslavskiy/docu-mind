from pydantic import BaseModel, Field
from typing import Union
from src.config.schemas.pipeline.document_processor import DefaultDocumentProcessorConfig
from src.config.schemas.pipeline.retriever import DenseRetrieverConfig


class PipelineConfig(BaseModel):
    document_processor: Union[DefaultDocumentProcessorConfig] = (Field(discriminator="type"))
    retriever: Union[DenseRetrieverConfig] = (Field(discriminator="type"))
