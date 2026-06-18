import logging
from abc import ABC, abstractmethod
from pathlib import Path
from src.core_schemas import Chunk
from src.indexing.loaders.base import BaseLoader
from src.indexing.chunkers.base import BaseChunker
from src.logger.logger_setup import get_logger


class BaseDocumentProcessor(ABC):
    def __init__(self, loaders: list[BaseLoader], chunker: BaseChunker, logger: logging.Logger = None, **kwargs):
        self.loaders = loaders
        self.chunker = chunker
        self.logger = logger if logger is not None else get_logger("pipeline")
        if logger is None:
            self.logger.disabled = True

    @abstractmethod
    def process(self, raw_dir: str | Path, show_progress_bar: bool = True) -> list[Chunk]:
        ...
