from abc import ABC, abstractmethod
from src.core.schemas import Chunk


class BaseGenerator(ABC):
    @abstractmethod
    def generate(self, question: str, context_chunks: list[Chunk]) -> str:
        ...
