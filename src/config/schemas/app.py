from pydantic import BaseModel, Field
from typing import Literal, Union, Annotated
from src.config.schemas.clients import (
    OllamaClientConfig,
    OpenAiClientConfig,
    GroqClientConfig,
    GoogleClientConfig,
)


class ApiConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = Field(8000, ge=1024, le=65535)


class EmbeddingModelConfig(BaseModel):
    name: str = "BAAI/bge-m3"
    device: str = Field("cuda", pattern=r"^(cpu|cuda(:\d+)?)$")


class PromptsConfig(BaseModel):
    answer_with_context: str = (
        "You are a technical documentation assistant.\n"
        "Answer the user's question based ONLY on the provided context.\n"
        "If the answer is not found in the context, say \"I don't have this information in the provided documents.\"\n"
        "Do not make up any facts or use your own knowledge.\n"
        "Answer in the same language as the user's question."

    )
    summarize: str = (
        "Summarize the following text in about {max_length} words. "
        "Keep all technical details, code examples, and key facts.\n\n{text}"
    )


class LLMConfig(BaseModel):
    client: Union[OllamaClientConfig, OpenAiClientConfig, GoogleClientConfig, GroqClientConfig] = (
        Field(discriminator="provider"))
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)


class ModelsConfig(BaseModel):
    embedding: EmbeddingModelConfig = Field(default_factory=EmbeddingModelConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)


class StorageConfig(BaseModel):
    type: Literal["faiss", "qdrant"] = "faiss"


class LoaderConfig(BaseModel):
    type: Literal["html", "pdf", "markdown", "text"] = "html"


class DataConfig(BaseModel):
    storage: StorageConfig = Field(default_factory=StorageConfig)
    loader: LoaderConfig = Field(default_factory=LoaderConfig)


class AppConfig(BaseModel):
    api: ApiConfig = Field(default_factory=ApiConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    data: DataConfig = Field(default_factory=DataConfig)
