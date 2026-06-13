from abc import ABC, abstractmethod
from src.core.schemas import Chunk


class BaseLLMModel(ABC):
    @abstractmethod
    def generate(self, question: str, context_chunks: list[Chunk]) -> str:
        ...

    @abstractmethod
    def summarize(self, text: str, max_length: int = 200) -> str:
        ...
