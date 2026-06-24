import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from documents_stores.base import BaseDocumentsStore
from src.configs.schemas.pipeline.documents_store import BaseDocumentsStoreConfig


def create_documents_store(config: BaseDocumentsStoreConfig) -> BaseDocumentsStore | None:
    if config.type == "disabled":
        return None

    elif config.type == "postgres":
        from documents_stores.implementations.postgres_store import PostgresDocumentsStore

        url = os.getenv("FULLTEXT_URL", None)
        if not url:
            raise ValueError("FULLTEXT_URL environment variable is required for PostgreSQL connection")

        engine = create_async_engine(url, echo=False)
        session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        documents_store_params = config.model_dump(exclude={"type"})
        return PostgresDocumentsStore(session_factory=session_factory, **documents_store_params)

    else:
        raise ValueError(f"Unknown documents store type: {config.type}")
