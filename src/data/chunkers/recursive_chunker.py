from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.core.schemas import Document, Chunk
from src.data.chunkers.base import BaseChunker
from src.config.schemas.pipeline import ChunkerConfig


class RecursiveChunker(BaseChunker):
    def __init__(self, config: ChunkerConfig):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=config.separators
        )

    def split(self, documents: list[Document]) -> list[Chunk]:
        lc_documents = [doc.to_langchain_document() for doc in documents]
        lc_chunks = self.splitter.split_documents(lc_documents)
        return [Chunk(content=chunk.page_content, metadata=chunk.metadata) for chunk in lc_chunks]