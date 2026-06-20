import logging
from abc import ABC, abstractmethod
from pathlib import Path
from src.core_schemas import Chunk
from src.indexing.loaders.base import BaseLoader
from src.indexing.chunkers.base import BaseChunker
from src.logger.logger_setup import get_logger


class BaseDocumentProcessor(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abstractmethod
    async def process(self, raw_dir: str | Path, show_progress_bar: bool = True) -> list[Chunk]:
        ...
