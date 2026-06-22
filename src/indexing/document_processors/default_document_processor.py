import logging
import uuid
from pathlib import Path
from src.core_schemas import Chunk
from src.indexing.document_processors.base import BaseDocumentProcessor
from src.indexing.documents_stores.base import BaseDocumentsStore
from src.indexing.loaders.base import BaseLoader
from src.indexing.chunkers.base import BaseChunker
from src.logger.logger_setup import get_logger


class DefaultDocumentProcessor(BaseDocumentProcessor):
    def __init__(
        self,
        loaders: list[BaseLoader],
        chunker: BaseChunker,
        documents_store: BaseDocumentsStore,
        logger: logging.Logger = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.loaders = loaders
        self.chunker = chunker
        self.documents_store = documents_store
        self.logger = logger if logger is not None else get_logger("pipeline")
        if logger is None:
            self.logger.disabled = True

    async def process(self, raw_dir: str | Path, show_progress_bar: bool = True) -> list[Chunk]:
        raw_dir = Path(raw_dir)
        all_docs = []

        if not raw_dir.exists():
            msg = f"Directory does not exist: {raw_dir}",
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

        docs_models = [(str(uuid.uuid4()), doc) for doc in all_docs]
        await self.documents_store.save_all(docs_models)

        self.logger.info("Total documents: %d", len(all_docs))
        chunks = self.chunker.split(all_docs)
        self.logger.info("Created %d chunks", len(chunks))
        return chunks
