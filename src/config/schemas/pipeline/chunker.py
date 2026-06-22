from pydantic import BaseModel, Field
from typing import Literal


class BaseChunkerConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class RecursiveChunkerConfig(BaseChunkerConfig):
    type: Literal["recursive"]
    chunk_size: int = Field(512, ge=128, le=4096)
    chunk_overlap: int = Field(64, ge=0, le=1024)
    separators: list[str] = ["\n\n", "\n", ". ", " ", ""]
