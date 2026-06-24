from src.logger.logger_setup import get_logger
from loaders.factory import create_loader
from chunkers.factory import create_chunker
from documents_stores.factory import create_documents_store
from document_processors.base import BaseDocumentProcessor
from src.configs.schemas.pipeline.document_processor import BaseDocumentProcessorConfig


def create_document_processor(config: BaseDocumentProcessorConfig) -> BaseDocumentProcessor | None:
    if config.type == "disabled":
        return None

    elif config.type == "default":
        from document_processors.implementations.default_document_processor import DefaultDocumentProcessor

        chunker = create_chunker(config=config.chunker)
        documents_store = create_documents_store(config=config.documents_store)
        logger = get_logger("pipeline")
        loaders = []
        for loader_type in config.loaders:
            loader = create_loader(loader_type=loader_type)
            loaders.append(loader)
        document_processor_params = config.model_dump(exclude={"type", "chunker", "loaders", "documents_store"})

        return DefaultDocumentProcessor(
            loaders=loaders,
            chunker=chunker,
            documents_store=documents_store,
            logger=logger,
            **document_processor_params
        )

    else:
        raise ValueError(f"Unknown document_processor type: {config.type}")
