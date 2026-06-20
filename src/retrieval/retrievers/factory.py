from config.schemas.pipeline.retriever import BaseRetrieverConfig, DenseRetrieverConfig
from retrieval.retrievers.base import BaseRetriever
from retrieval.embedders.factory import create_embedder
from retrieval.vector_stores.factory import create_vector_store


def create_retriever(config: BaseRetrieverConfig) -> BaseRetriever:
    if config.type == "dense" and isinstance(config, DenseRetrieverConfig):
        from retrieval.retrievers.dense_retriever import DenseRetriever

        retriever_params = config.model_dump(exclude={"type", "embedder", "vector_storage"})
        embedder = create_embedder(config.embedder)
        store = create_vector_store(config.vector_storage)

        return DenseRetriever(embedder=embedder, store=store, **retriever_params)

    else:
        raise ValueError(f"Unknown retriever type: {config.type}")
