import json
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.indexing.documents_stores.base import BaseDocumentsStore
from src.indexing.documents_stores.models import DocumentModel
from src.core_schemas import Document


class PostgresDocumentsStore(BaseDocumentsStore):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], **kwargs):
        super().__init__(**kwargs)
        self.session_factory = session_factory

    async def save(self, doc_id: str, doc: Document) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                await session.merge(
                    DocumentModel(
                        id=doc_id,
                        description=doc.description,
                        content=doc.content,
                        meta_json=json.dumps(doc.metadata),
                    )
                )

    async def save_all(self, docs: list[(str, Document)]) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                for doc_id, doc in docs:
                    await session.merge(
                        DocumentModel(
                            id=doc_id,
                            description=doc.description,
                            content=doc.content,
                            meta_json=json.dumps(doc.metadata),
                        )
                    )

    async def get(self, doc_id: str) -> Document | None:
        async with self.session_factory() as session:
            row = await session.get(DocumentModel, doc_id)
            if row is None:
                return None
            metadata = json.loads(row.meta_json) if row.meta_json else {}
            return Document(content=row.content, description=row.description, metadata=metadata)

    async def get_all_base_info(self) -> list[dict[str, str]]:
        async with self.session_factory() as session:
            stmt = select(DocumentModel.id, DocumentModel.description)
            result = await session.execute(stmt)
            return [{"id": row.id, "description": row.description} for row in result]

    async def delete(self, doc_id: str) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                await session.execute(
                    delete(DocumentModel).where(DocumentModel.id == doc_id)
                )
