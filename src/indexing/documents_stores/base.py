from abc import ABC, abstractmethod
from src.core_schemas import Document
from src.indexing.documents_stores.models import DocumentModel


class BaseDocumentsStore(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abstractmethod
    async def save(self, doc_id: str, document: Document) -> None:
        ...

    @abstractmethod
    async def save_all(self, documents: list[(str, Document)]) -> None:
        ...

    @abstractmethod
    async def get(self, doc_id: str) -> Document | None:
        ...

    @abstractmethod
    async def get_base_info(self) -> list[dict[str, str]]:
        ...

    @abstractmethod
    async def delete(self, doc_id: str) -> None:
        ...
