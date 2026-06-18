import logging
from src.indexing.loaders.factory import create_loader
from src.indexing.chunkers.factory import create_chunker
from src.indexing.document_processors.base import BaseDocumentProcessor
from src.config.schemas.pipeline.document_processor import BaseDocumentProcessorConfig


def create_document_processor(
    config: BaseDocumentProcessorConfig,
    logger: logging.Logger = None
) -> BaseDocumentProcessor:

    loaders = []
    for loader_type in config.loaders:
        loader = create_loader(loader_type=loader_type, logger=logger)
        loaders.append(loader)

    chunker = create_chunker(config.chunker)
    document_processor_params = config.model_dump(exclude={"type", "chunker", "loaders"})

    if config.type == "default":
        from src.indexing.document_processors.default_document_processor import DefaultDocumentProcessor
        return DefaultDocumentProcessor(loaders=loaders, chunker=chunker, logger=logger, **document_processor_params)
    else:
        raise ValueError(f"Unknown document_processor type: {config.type}")
