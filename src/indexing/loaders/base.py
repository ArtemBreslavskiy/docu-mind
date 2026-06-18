import logging
from abc import ABC, abstractmethod
from pathlib import Path
from src.logger.logger_setup import get_logger
from core_schemas import Document


class BaseLoader(ABC):
    def __init__(self, logger: logging.Logger = None, **kwargs):
        self.logger = logger if logger is not None else get_logger("pipeline")
        if logger is None:
            self.logger.disabled = True
        self.kwargs = kwargs
    
    @abstractmethod
    def load(self, raw_dir: str | Path, show_progress_bar: bool = True) -> list[Document]:
        ...
