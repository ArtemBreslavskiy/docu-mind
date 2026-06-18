from retrieval.vector_store.base import BaseVectorStore
from config.schemas.app.storage import BaseStorageConfig
from paths.project_paths import ProjectPaths


def create_vector_store(config: BaseStorageConfig) -> BaseVectorStore:
    paths = ProjectPaths()
    store_params = config.model_dump(exclude={"type"})

    if config.type == "faiss":
        from retrieval.vector_store.faiss_store import FAISSStore
        return FAISSStore(log_dir=paths.PROCESSED, **store_params)
    else:
        raise ValueError(f"Unknown vector store type: {config.type}")
