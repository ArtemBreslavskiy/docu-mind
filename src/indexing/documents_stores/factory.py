import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.indexing.documents_stores.base import BaseDocumentsStore
from src.config.schemas.pipeline.documents_store import BaseDocumentsStoreConfig, PostgresDocumentsStoreConfig


def create_documents_store(config: BaseDocumentsStoreConfig) -> BaseDocumentsStore:
    if config.type == "postgres":
        from src.indexing.documents_stores.postgres_store import PostgresDocumentsStore

        host = os.getenv("FULLTEXT_HOST", "localhost")
        port = os.getenv("FULLTEXT_PORT", "5432")
        db = os.getenv("FULLTEXT_DB", "documind")
        user = os.getenv("FULLTEXT_USER", "postgres")
        password = os.getenv("FULLTEXT_PASSWORD", "")
        url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

        engine = create_async_engine(url, echo=False)
        session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        return PostgresDocumentsStore(session_factory=session_factory)

    else:
        raise ValueError(f"Unknown documents_store type: {config.type}")