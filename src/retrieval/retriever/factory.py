from config.schemas.pipeline.retriever import BaseRetrieverConfig
from retrieval.retriever.base import BaseRetriever
from retrieval.embedder.base import BaseEmbedder
from retrieval.vector_store.base import BaseVectorStore


def create_retriever(config: BaseRetrieverConfig, embedder: BaseEmbedder, store: BaseVectorStore) -> BaseRetriever:
    retriever_params = config.model_dump(exclude={"type"})

    if config.type == "dense":
        from retrieval.retriever.dense_retriever import DenseRetriever
        return DenseRetriever(embedder=embedder, store=store, **retriever_params)
    else:
        raise ValueError(f"Unknown retriever type: {config.type}")
