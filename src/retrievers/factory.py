from configs.schemas.pipeline.retriever import BaseRetrieverConfig
from retrievers.base import BaseRetriever
from embedders.factory import create_embedder
from vector_stores.factory import create_vector_store


def create_retriever(config: BaseRetrieverConfig) -> BaseRetriever | None:
    if config.type == "disabled":
        return None

    elif config.type == "dense":
        from retrievers.implementations.dense_retriever import DenseRetriever

        embedder = create_embedder(config.embedder)
        if not embedder:
            raise ValueError("Embedder cannot be disabled")

        vector_store = create_vector_store(config.vector_storage)
        if not vector_store:
            raise ValueError("Vector store cannot be disabled")

        retriever_params = config.model_dump(exclude={"type", "embedder", "vector_storage"})
        return DenseRetriever(embedder=embedder, store=vector_store, **retriever_params)

    else:
        raise ValueError(f"Unknown retriever type: {config.type}")
