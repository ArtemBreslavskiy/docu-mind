from pydantic import BaseModel, Field
from typing import Literal


class ApiConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = Field(8000, ge=1024, le=65535)


class EmbeddingModelConfig(BaseModel):
    name: str = "BAAI/bge-m3"
    device: str = Field("cuda", pattern=r"^(cpu|cuda(:\d+)?)$")


class LLMConfig(BaseModel):
    pass


class ModelsConfig(BaseModel):
    embedding: EmbeddingModelConfig
    llm: LLMConfig


class StorageConfig(BaseModel):
    type: Literal["faiss", "qdrant"] = "faiss"


class LoaderConfig(BaseModel):
    type: Literal["html", "pdf", "markdown", "text"] = "html"


class DataConfig(BaseModel):
    storage: StorageConfig
    loader: LoaderConfig


class AppConfig(BaseModel):
    api: ApiConfig
    models: ModelsConfig
    data: DataConfig
