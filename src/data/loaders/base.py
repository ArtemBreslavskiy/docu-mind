from abc import ABC, abstractmethod
from typing import Union
from pathlib import Path
from src.core.schemas import Document


class BaseLoader(ABC):
    @abstractmethod
    def load(self, raw_dir: Union[str, Path], show_progress_bar: bool = True) -> list[Document]:
        ...
