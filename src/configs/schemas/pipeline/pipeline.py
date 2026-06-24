import src.configs.schemas.pipeline.document_processor as document_processor
import src.configs.schemas.pipeline.vectors_builder as vectors_builder
import src.configs.schemas.pipeline.graph_builder as graph_builder
import src.configs.schemas.pipeline.retriever as retriever
import src.configs.schemas.pipeline.sql_db as sql_db
from pydantic import BaseModel, Field
from typing import Union, Annotated


class PipelineConfig(BaseModel):
    document_processor: Union[
        document_processor.DisabledDocumentProcessorConfig,
        document_processor.DefaultDocumentProcessorConfig
    ] = Field(discriminator="type")
    vectors_builder: Union[
        vectors_builder.DisabledVectorsBuilderConfig,
        vectors_builder.DefaultVectorsBuilderConfig,
    ] = Field(discriminator="type")
    retriever: Union[
        retriever.DisabledRetrieverConfig,
        retriever.DenseRetrieverConfig,
    ] = Field(discriminator="type")
    graph_builder: Union[
        graph_builder.DisabledGraphBuilderConfig,
        graph_builder.LLMBasedGraphBuilderConfig,
    ] = Field(discriminator="type")
    sql_databases: list[Annotated[Union[
        sql_db.DisabledSQLDatabaseConfig,
        sql_db.PostgresSQLDatabaseConfig,
    ], Field(discriminator="type")]] = Field(default_factory=list)
