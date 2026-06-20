import json
from retrieval.retrievers.base import BaseRetriever
from retrieval.embedders.base import BaseEmbedder
from retrieval.vector_stores.base import BaseVectorStore
from core_schemas import SearchResult


class DenseRetriever(BaseRetriever):
    def __init__(self, embedder: BaseEmbedder, store: BaseVectorStore, filter_oversample_factor: float = 3, **kwargs):
        super().__init__(**kwargs)
        self.embedder = embedder
        self.store = store
        self.filter_oversample_factor = filter_oversample_factor

    def retrieve(self, query: str, k: int = 5) -> list[SearchResult]:
        query_emb = self.embedder.embed([query])[0]
        chunk_score_pairs = self.store.search(query_emb, k=k)
        return [SearchResult(chunk=chunk, score=score) for chunk, score in chunk_score_pairs]

    def retrieve_with_filter(self, query, filter_key=None, filter_value=None, filter_json=None, k=5) \
            -> list[SearchResult]:
        query_emb = self.embedder.embed([query])[0]
        chunk_score_pairs = self.store.search(query_emb, k=int(k * self.filter_oversample_factor))

        conditions = None
        if filter_json:
            try:
                conditions = json.loads(filter_json)
            except json.JSONDecodeError as ex:
                raise ValueError(f"Invalid filter_json: not valid JSON. Got: {filter_json}")

            if not self._validate_filter_structure(conditions):
                raise ValueError(f"Invalid filter_json structure. Allowed keys: 'and', 'or', 'key' with 'values' list.")

        filtered = []
        for chunk, score in chunk_score_pairs:
            metadata = chunk.metadata
            if filter_key and filter_value:
                if metadata.get(filter_key) != filter_value:
                    continue
            if conditions:
                if not self._check_metadata_conditions(metadata, conditions):
                    continue
            filtered.append(SearchResult(chunk=chunk, score=score))
            if len(filtered) >= k:
                break
        return filtered

    def _validate_filter_structure(self, node: dict) -> bool:
        if "and" in node:
            return isinstance(node["and"], list) and all(self._validate_filter_structure(c) for c in node["and"])
        if "or" in node:
            return isinstance(node["or"], list) and all(self._validate_filter_structure(c) for c in node["or"])
        if "key" in node:
            return isinstance(node.get("values"), list)
        return False

    def _check_metadata_conditions(self, metadata: dict, conditions: dict) -> bool:
        if "and" in conditions:
            return all(self._check_metadata_conditions(metadata, c) for c in conditions["and"])
        if "or" in conditions:
            return any(self._check_metadata_conditions(metadata, c) for c in conditions["or"])
        if "key" in conditions:
            key = conditions["key"]
            values = conditions.get("values", [])
            return metadata.get(key) in values
        return False
