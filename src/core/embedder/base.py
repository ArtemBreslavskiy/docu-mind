from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    @abstractmethod
    def embed(self, texts: list[str], show_progress_bar: bool = True) -> list[list[float]]:
        ...
