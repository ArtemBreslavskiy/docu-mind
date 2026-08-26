import src.data.db_adapters.base as base
from data.db.nosql.vector.faiss.reader import FAISSReader
from src.core.embedders.base import BaseEmbedder
from typing import Any


class FAISSAdapter(
    base.BaseAdapter,
    base.SearchSemanticCallable,
    base.GetDistinctValuesCallable,
    base.CountRecordsCallable,
    base.GetSchemaInfoCallable,
):
    def __init__(self, reader: FAISSReader, embedder: BaseEmbedder):
        self.reader = reader
        self.embedder = embedder

    async def search_semantic(self, table: str, field: str, query: str, limit: int = 10) -> list[dict]:
        if self.embedder is None:
            raise NotImplementedError("search_text requires an embedder")
        vectors = await self.embedder.embed([query], show_progress_bar=False)
        vector = vectors[0]
        results = await self.reader.search(query_vector=vector, top_k=limit)
        return [
            {
                "id": res.id,
                "chunk": res.chunk.model_dump() if hasattr(res.chunk, "model_dump") else res.chunk,
                "score": res.score,
            }
            for res in results
        ]

    async def get_distinct_values(self, table: str, field: str, limit: int = 20) -> list[Any]:
        if not self.reader.chunks:
            self.reader._load()
        values = set()
        for chunk in self.reader.chunks:
            if chunk.metadata and field in chunk.metadata:
                values.add(chunk.metadata[field])
        return list(values)[:limit]

    async def count_records(self, table: str = "", filter: dict | None = None) -> int:
        if filter is None:
            return self.reader.index.ntotal
        count = 0
        for chunk in self.reader.chunks:
            match = True
            for k, v in filter.items():
                if chunk.metadata.get(k) != v:
                    match = False
                    break
            if match:
                count += 1
        return count
