from src.storage.vector_store.base import BaseVectorStore
from src.storage.vector_store.faiss_store import FAISSStore
from src.config.schemas.app import StorageConfig
from paths.project_paths import ProjectPaths


def create_vector_store(config: StorageConfig) -> BaseVectorStore:
    paths = ProjectPaths()

    if config.type == "faiss":
        return FAISSStore(paths.PROCESSED)
    else:
        raise ValueError(f"Unknown vector store type: {config.type}")
