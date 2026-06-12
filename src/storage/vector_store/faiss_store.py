import faiss
import numpy as np
import json
from pathlib import Path
from typing import Union, Optional
from src.storage.vector_store.base import BaseVectorStore
from src.core.schemas import Chunk


class FAISSStore(BaseVectorStore):
    def __init__(self, log_dir: Union[str, Path]):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.store_path = self.log_dir / "store"
        self.json_path = self.log_dir / "chunks.json"

        self.index: Optional[faiss.Index] = None
        self.chunks: list[Chunk] = []

    def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("The number of chunks and vectors must match")

        self.chunks = chunks

        dim = len(embeddings[0])
        self.index = faiss.IndexFlatIP(dim)

        vectors = np.array(embeddings, dtype="float32")
        self.index.add(vectors)

        self._save()

    def search(self, query_embedding: list[float], k: int = 5) -> list[tuple[Chunk, float]]:
        if self.index is None:
            self._load()

        vector = np.array([query_embedding], dtype="float32")
        scores, indices = self.index.search(vector, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1:
                results.append((self.chunks[idx], float(score)))
        return results

    def _save(self):
        self.log_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.store_path))

        chunk_data = [chunk.model_dump() for chunk in self.chunks]
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)

    def _load(self):
        self.index = faiss.read_index(str(self.store_path))

        with open(self.json_path, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)
        self.chunks = [Chunk(**item) for item in chunks_data]