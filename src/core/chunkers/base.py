from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any
from core.schemas import Document


class Chunk(BaseModel):
    content: str
    metadata: dict[str, Any]
    embedding: list[float] | None = None


class BaseChunker(ABC):
    @abstractmethod
    def split(self, documents: list[Document]) -> list[Chunk]:
        ...
