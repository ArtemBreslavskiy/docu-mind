from src.logger.logger_setup import get_logger
from src.indexing.loaders.factory import create_loader
from src.indexing.chunkers.factory import create_chunker
from src.indexing.documents_stores.factory import create_documents_store
from src.indexing.document_processors.base import BaseDocumentProcessor
from src.config.schemas.pipeline.document_processor import BaseDocumentProcessorConfig, DefaultDocumentProcessorConfig


def create_document_processor(
    config: BaseDocumentProcessorConfig,
) -> BaseDocumentProcessor:
    if config.type == "default":
        from src.indexing.document_processors.default_document_processor import DefaultDocumentProcessor

        document_processor_params = config.model_dump(exclude={"type", "chunker", "loaders", "documents_store"})
        chunker = create_chunker(config=config.chunker)
        documents_store = create_documents_store(config=config.documents_store)
        logger = get_logger("pipeline")
        loaders = []
        for loader_type in config.loaders:
            loader = create_loader(loader_type=loader_type)
            loaders.append(loader)

        return DefaultDocumentProcessor(
            loaders=loaders,
            chunker=chunker,
            documents_store=documents_store,
            logger=logger,
            **document_processor_params
        )
    else:
        raise ValueError(f"Unknown document_processor type: {config.type}")
