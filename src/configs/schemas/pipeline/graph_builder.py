import src.configs.schemas.pipeline.embedder as embedder
import src.configs.schemas.pipeline.graph_store as graph_store
import src.configs.schemas.pipeline.llm as llm
from pydantic import BaseModel, Field
from typing import Literal, Union


class BaseGraphBuilderConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class DisabledGraphBuilderConfig(BaseGraphBuilderConfig):
    type: Literal["disabled"]


class LLMBasedGraphBuilderConfig(BaseGraphBuilderConfig):
    type: Literal["llm_based"]
    graph_store: Union[
        graph_store.DisabledGraphStoreConfig,
        graph_store.Neo4jGraphStoreConfig,
    ] = Field(discriminator="type")
    embedder: Union[
        embedder.DisabledEmbedderConfig,
        embedder.SentenceTransformerEmbedderConfig,
    ] = Field(discriminator="type")
    llm: Union[
        llm.DisabledClientConfig,
        llm.OllamaClientConfig,
        llm.OpenAiClientConfig,
        llm.GoogleClientConfig,
        llm.GroqClientConfig,
    ] = Field(discriminator="provider")
    batch_size: int = Field(10, gt=0)
    similarity_threshold: float = Field(0.85, ge=0.0, le=1.0)
