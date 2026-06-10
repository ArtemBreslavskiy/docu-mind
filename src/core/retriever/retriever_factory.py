from src.config.schemas.pipeline import RetrieverConfig
from src.core.retriever.base import BaseRetriever
from src.core.retriever.dense_retriever import DenseRetriever
from src.core.embedder.base import BaseEmbedder
from src.storage.vector_store.base import BaseVectorStore


def create_retriever(config: RetrieverConfig, embedder: BaseEmbedder, store: BaseVectorStore) -> BaseRetriever:
    if config.type == "dense":
        return DenseRetriever(embedder, store)
    else:
        raise ValueError(f"Unknown retriever type: {config.type}")
