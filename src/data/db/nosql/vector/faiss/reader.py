import json
import faiss
import numpy as np
from pathlib import Path
from typing import Any
from src.core.chunkers.base import Chunk
from src.data.db.nosql.reader.vector.base import BaseVectorReader, VectorSearchResult


class FAISSReader(BaseVectorReader):
    def __init__(self, log_dir: str | Path, **kwargs):
        super().__init__(**kwargs)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.store_path = self.log_dir / "store"
        self.json_path = self.log_dir / "chunks.json"

        self.index: faiss.Index | None = None
        self.chunks: list[Chunk] = []

        self.index = faiss.read_index(str(self.store_path))
        with open(self.json_path, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)
        self.chunks = [Chunk(**item) for item in chunks_data]

    async def execute_read(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError("FAISS does not support read queries")

    async def get_schema_info(self) -> str:
        if self.index is None:
            self._load()

        lines = [
            f"Vector store",
            f"Dimension: {self.index.d}",
            f"Total vectors: {self.index.ntotal}",
        ]
        if self.chunks:
            sample_meta = self.chunks[0].metadata or {}
            if sample_meta:
                fields = ", ".join(sample_meta.keys())
                lines.append(f"Metadata fields (example): {fields}")
        return "\n".join(lines)

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None
    ) -> list[VectorSearchResult]:
        if self.index is None:
            self._load()

        q = np.array([query_vector], dtype=np.float32)
        distances, indices = self.index.search(q, top_k)

        results = []
        for score, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            if idx >= len(self.chunks):
                continue
            chunk = self.chunks[idx]
            if filter is not None:
                match = True
                for k, v in filter.items():
                    if chunk.metadata.get(k) != v:
                        match = False
                        break
                if not match:
                    continue
            results.append(VectorSearchResult(
                id=str(idx),
                chunk=chunk,
                score=float(score)
            ))
        return results
