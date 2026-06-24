from abc import ABC, abstractmethod
from pathlib import Path
from core_schemas import Document


class BaseLoader(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    
    @abstractmethod
    def load(self, raw_dir: str | Path, show_progress_bar: bool = True) -> list[Document]:
        ...
