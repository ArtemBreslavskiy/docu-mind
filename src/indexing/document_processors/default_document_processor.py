import logging
from pathlib import Path
from src.core_schemas import Chunk
from src.indexing.document_processors.base import BaseDocumentProcessor
from src.indexing.loaders.base import BaseLoader
from src.indexing.chunkers.base import BaseChunker


class DefaultDocumentProcessor(BaseDocumentProcessor):
    def __init__(self, loaders: list[BaseLoader], chunker: BaseChunker, logger: logging.Logger = None, **kwargs):
        super().__init__(loaders=loaders, chunker=chunker, logger=logger, **kwargs)

    def process(self, raw_dir: str | Path, show_progress_bar: bool = True) -> list[Chunk]:
        raw_dir = Path(raw_dir)
        all_docs = []

        if not raw_dir.exists():
            msg = "Directory does not exist: %s", raw_dir
            self.logger.error(msg)
            raise FileNotFoundError(msg)
        self.logger.info("Starting document processing from %s", raw_dir)

        for loader in self.loaders:
            docs = loader.load(raw_dir=raw_dir, show_progress_bar=show_progress_bar)
            if docs:
                self.logger.info("Loader %s returned %d documents", loader.__class__.__name__, len(docs))
                all_docs.extend(docs)

        if not all_docs:
            self.logger.warning("No documents found")
            return []

        self.logger.info("Total documents: %d", len(all_docs))
        chunks = self.chunker.split(all_docs)
        self.logger.info("Created %d chunks", len(chunks))
        return chunks
