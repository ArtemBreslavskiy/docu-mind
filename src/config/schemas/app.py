from pydantic import BaseModel, Field
from typing import Literal, Optional


class ApiConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = Field(8000, ge=1024, le=65535)


class EmbeddingModelConfig(BaseModel):
    name: str = "BAAI/bge-m3"
    device: str = Field("cuda", pattern=r"^(cpu|cuda(:\d+)?)$")


class LLMConfig(BaseModel):
    provider: Literal["ollama", "openai"] = "ollama"
    model: str = "llama3.2:3b"
    temperature: float = Field(0.1, ge=0.0, le=2.0)
    base_url: str = "http://localhost:11434"
    max_tokens: int = Field(512, ge=1, le=4096)
    system_prompt: str = (
        "You are a technical documentation assistant.\n"
        "Answer the user's question based ONLY on the provided context.\n"
        "If the answer is not found in the context, say \"I don't have this information in the provided documents.\"\n"
        "Do not make up any facts or use your own knowledge.\n"
        "Answer in the same language as the user's question."
    )


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
