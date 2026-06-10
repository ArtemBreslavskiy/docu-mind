from pydantic import BaseModel, Field
from typing import Optional


class ApiConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = Field(8000, ge=1024, le=65535)


class EmbeddingModelConfig(BaseModel):
    name: str = "BAAI/bge-m3"
    device: str = Field("cuda", pattern=r"^(cpu|cuda(:\d+)?)$")


class LLMConfig(BaseModel):
    pass


class ChunkerConfig(BaseModel):
    type: str = "recursive"
    chunk_size: int = Field(512, ge=128, le=8192)
    chunk_overlap: int = Field(50, ge=0, le=2048)
    separators: list[str] = ["\n\n", "\n", ". ", " ", ""]


class DataConfig(BaseModel):
    raw_dir: str = "data/raw"
    faiss_index_path: str = "data/faiss_index"
    chunker: ChunkerConfig = ChunkerConfig()


class ModelsConfig(BaseModel):
    embedding: EmbeddingModelConfig
    llm: Optional[LLMConfig] = None


class AppConfig(BaseModel):
    api: ApiConfig
    models: ModelsConfig
    data: DataConfig
