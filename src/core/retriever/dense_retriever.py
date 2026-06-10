from src.core.retriever.base import BaseRetriever
from src.core.embedder.base import BaseEmbedder
from src.storage.vector_store.base import BaseVectorStore
from src.core.schemas import SearchResult


class DenseRetriever(BaseRetriever):
    def __init__(self, embedder: BaseEmbedder, store: BaseVectorStore):
        self.embedder = embedder
        self.store = store

    def retrieve(self, query: str, k: int = 5) -> list[SearchResult]:
        query_emb = self.embedder.embed([query])[0]
        chunk_score_pairs = self.store.search(query_emb, k)
        return [SearchResult(chunk=chunk, score=score) for chunk, score in chunk_score_pairs]
