from langchain_text_splitters import RecursiveCharacterTextSplitter
from core_schemas import Document, Chunk
from indexing.chunkers.base import BaseChunker


class RecursiveChunker(BaseChunker):
    def __init__(self, chunk_size: int, chunk_overlap: int, separators: list[str], **kwargs):
        super().__init__(**kwargs)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
        )

    def split(self, documents: list[Document]) -> list[Chunk]:
        lc_documents = [doc.to_langchain_document() for doc in documents]
        lc_chunks = self.splitter.split_documents(lc_documents)
        return [Chunk(content=chunk.page_content, metadata=chunk.metadata) for chunk in lc_chunks]