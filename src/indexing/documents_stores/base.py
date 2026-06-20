from abc import ABC, abstractmethod
from src.core_schemas import Document


class BaseDocumentsStore(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abstractmethod
    async def save(self, doc_id: str, doc: Document) -> None:
        ...

    @abstractmethod
    async def save_all(self, docs: list[tuple[str, Document]]) -> None:
        ...

    @abstractmethod
    async def get(self, doc_id: str) -> Document | None:
        ...

    @abstractmethod
    async def delete(self, doc_id: str) -> None:
        ...
