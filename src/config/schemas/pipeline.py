from pydantic import BaseModel, Field
from typing import Literal


class ChunkerConfig(BaseModel):
    type: Literal["recursive", "semantic"] = "recursive"
    chunk_size: int = Field(512, ge=128, le=4096)
    chunk_overlap: int = Field(64, ge=0, le=1024)
    separators: list[str] = ["\n\n", "\n", ". ", " ", ""]


class RetrieverConfig(BaseModel):
    type: Literal["dense", "hybrid"] = "dense"
    top_k: int = Field(5, ge=1, le=100)
    filter_oversample_factor: int = Field(
        4, 
        ge=2,
        le=10,
        description="Multiplier for initial retrieval count before filtering"
    )


class PipelineConfig(BaseModel):
    chunker: ChunkerConfig = Field(default_factory=ChunkerConfig)
    retriever: RetrieverConfig = Field(default_factory=RetrieverConfig)
