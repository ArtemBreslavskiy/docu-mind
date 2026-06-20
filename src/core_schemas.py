from pydantic import BaseModel
from typing import Any, Optional
from langchain_core.documents import Document as LCDocument


class Document(BaseModel):
    content: str
    metadata: dict[str, Any]

    def to_langchain_document(self) -> LCDocument:
        return LCDocument(page_content=self.content, metadata=self.metadata)


class Chunk(BaseModel):
    content: str
    metadata: dict[str, Any]
    embedding: Optional[list[float]] = None


class SearchResult(BaseModel):
    chunk: Chunk
    score: float
