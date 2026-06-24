from vector_stores.base import BaseVectorStore
from configs.schemas.pipeline.vector_store import BaseVectorStoreConfig
from paths.project_paths import ProjectPaths


def create_vector_store(config: BaseVectorStoreConfig) -> BaseVectorStore | None:
    if config.type == "disabled":
        return None

    elif config.type == "faiss":
        from vector_stores.implementations.faiss_store import FAISSStore

        store_params = config.model_dump(exclude={"type"})
        paths = ProjectPaths()

        return FAISSStore(log_dir=paths.PROCESSED, **store_params)

    else:
        raise ValueError(f"Unknown vector store type: {config.type}")
