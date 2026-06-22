from retrieval.vector_stores.base import BaseVectorStore
from config.schemas.pipeline.storage import BaseStorageConfig, FAISSStorageConfig
from paths.project_paths import ProjectPaths


def create_vector_store(config: BaseStorageConfig) -> BaseVectorStore:
    if config.type == "faiss":
        from retrieval.vector_stores.faiss_store import FAISSStore

        store_params = config.model_dump(exclude={"type"})
        paths = ProjectPaths()

        return FAISSStore(log_dir=paths.PROCESSED, **store_params)

    else:
        raise ValueError(f"Unknown vector store type: {config.type}")
