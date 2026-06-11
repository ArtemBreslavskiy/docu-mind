from pydantic import BaseModel, Field
from typing import Literal, Optional


class ApiConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = Field(8000, ge=1024, le=65535)


class EmbeddingModelConfig(BaseModel):
    name: str = "BAAI/bge-m3"
    device: str = Field("cuda", pattern=r"^(cpu|cuda(:\d+)?)$")


class LLMConfig(BaseModel):
    pass


class ModelsConfig(BaseModel):
    embedding: EmbeddingModelConfig = Field(default_factory=EmbeddingModelConfig)
    llm: Optional[LLMConfig] = None


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
