import logging
from utils.logger_setup import get_logger
from core.schemas import Chunk
from data.vectors_builders.base import BaseVectorsBuilder
from core.embedders.base import BaseEmbedder
from data.vector_db.base import BaseVectorStore


class DefaultVectorsBuilder(BaseVectorsBuilder):
    def __init__(
        self, embedder: BaseEmbedder,
        vector_store: BaseVectorStore,
        logger: logging.Logger | None = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.embedder = embedder
        self.vector_store = vector_store
        self.logger = logger if logger is not None else get_logger("pipeline")
        if logger is None:
            self.logger.disabled = True

    def build(self, chunks: list[Chunk], show_progress_bar: bool = True) -> None:
        texts = [chunk.content for chunk in chunks]
        self.logger.info("Generating embeddings for %d chunks...", len(texts))
        try:
            embeddings = self.embedder.embed(texts=texts, show_progress_bar=show_progress_bar)
        except Exception as e:
            self.logger.error("Failed to generate embeddings: %s", e)
            raise
        self.logger.info("Embeddings generated")

        self.logger.info("Saving chunks to vector store...")
        self.vector_store.add(chunks, embeddings)
        self.logger.info("Index creation completed. Total chunks: %d", len(chunks))
