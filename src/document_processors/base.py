from abc import ABC, abstractmethod
from pathlib import Path
from src.core_schemas import Chunk


class BaseDocumentProcessor(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abstractmethod
    async def process(self, raw_dir: str | Path, show_progress_bar: bool = True) -> list[Chunk]:
        ...
