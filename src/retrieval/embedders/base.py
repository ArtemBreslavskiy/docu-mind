from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abstractmethod
    def embed(self, texts: list[str], show_progress_bar: bool = True) -> list[list[float]]:
        ...
