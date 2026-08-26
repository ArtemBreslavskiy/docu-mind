import src.configs.schemas.pipeline.document_processor as document_processors
import configs.schemas.pipeline.vector.builder as vectors_builders
import configs.schemas.pipeline.graph.builder as graph_builders
import src.configs.schemas.pipeline.retriever as retrievers
import configs.schemas.pipeline.sql_reader as sql_reader
from pydantic import BaseModel, Field
from typing import Union, Annotated


class PipelineConfig(BaseModel):
    document_processor: Union[
        document_processors.DisabledDocumentProcessorConfig,
        document_processors.DefaultDocumentProcessorConfig
    ] = Field(discriminator="type")
    vectors_builder: Union[
        vectors_builders.DisabledVectorsBuilderConfig,
        vectors_builders.DefaultVectorsBuilderConfig,
    ] = Field(discriminator="type")
    retriever: Union[
        retrievers.DisabledRetrieverConfig,
        retrievers.DenseRetrieverConfig,
    ] = Field(discriminator="type")
    graph_builder: Union[
        graph_builders.DisabledGraphBuilderConfig,
        graph_builders.LLMBasedGraphBuilderConfig,
    ] = Field(discriminator="type")
    sql_databases: list[Annotated[Union[
        sql_reader.DisabledSQLReaderConfig,
        sql_reader.PostgresReaderConfig,
    ], Field(discriminator="type")]] = Field(default_factory=list)
