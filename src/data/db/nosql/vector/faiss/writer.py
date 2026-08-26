import json
import faiss
import numpy as np
from pathlib import Path
from typing import Any
from src.core.chunkers.base import Chunk
from data.db.nosql.vector.base import (
    BaseVectorWriter,
    VectorAdd,
    VectorUpdate,
    VectorWriteResponse,
)


class FAISSWriter(BaseVectorWriter):
    def __init__(self, log_dir: str | Path, **kwargs):
        super().__init__(**kwargs)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.store_path = self.log_dir / "store"
        self.json_path = self.log_dir / "chunks.json"

        self.entries: list[dict[str, Any]] = []
        self.index: faiss.Index | None = None

        self.index = faiss.read_index(str(self.store_path))
        with open(self.json_path, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)
        self.chunks = [Chunk(**item) for item in chunks_data]

    def _save(self) -> None:
        if self.index is None:
            if self.store_path.exists():
                self.store_path.unlink()
            if self.json_path.exists():
                self.json_path.unlink()
            return

        faiss.write_index(self.index, str(self.store_path))
        data_to_save = []
        for entry in self.entries:
            data_to_save.append({
                "id": entry["id"],
                "metadata": entry["metadata"],
            })
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)

    def _rebuild_index(self) -> None:
        if not self.entries:
            self.index = None
            return
        dim = len(self.entries[0]["vector"])
        self.index = faiss.IndexFlatIP(dim)
        vectors = np.array([entry["vector"] for entry in self.entries], dtype=np.float32)
        self.index.add(vectors)

    def _find_entry_index(self, vector_id: str) -> int | None:
        for i, entry in enumerate(self.entries):
            if entry["id"] == vector_id:
                return i
        return None

    @staticmethod
    def _make_response(result_id: str | None = None, error: str | None = None) -> VectorWriteResponse:
        if error:
            return VectorWriteResponse(id=None, error=error)
        return VectorWriteResponse(id=result_id, error=None)

    async def write_query(self, query: str, params: dict | None = None) -> list[dict]:
        raise NotImplementedError("FAISS does not support write queries")

    async def begin_transaction(self) -> None:
        raise NotImplementedError("FAISS does not support transactions.")

    async def commit_transaction(self) -> None:
        raise NotImplementedError("FAISS does not support transactions.")

    async def rollback_transaction(self) -> None:
        raise NotImplementedError("FAISS does not support transactions.")

    async def close(self) -> None:
        self._save()
        self.index = None
        self.entries = []

    async def add_vector(
        self,
        vector: list[float],
        metadata: dict[str, Any],
        vector_id: str | None = None
    ) -> VectorWriteResponse:
        if vector_id is None:
            vector_id = str(len(self.entries))
        else:
            if self._find_entry_index(vector_id) is not None:
                return self._make_response(error=f"Vector with id {vector_id} already exists")

        new_entry = {
            "id": vector_id,
            "vector": vector,
            "metadata": metadata
        }
        self.entries.append(new_entry)
        self._rebuild_index()
        self._save()
        return self._make_response(vector_id)

    async def update_vector(
        self,
        vector_id: str,
        vector: list[float] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> VectorWriteResponse:
        idx = self._find_entry_index(vector_id)
        if idx is None:
            return self._make_response(error=f"Vector with id {vector_id} not found")

        if vector is not None:
            self.entries[idx]["vector"] = vector
        if metadata is not None:
            self.entries[idx]["metadata"] = metadata

        self._rebuild_index()
        self._save()
        return self._make_response(vector_id)

    async def delete_vector(self, vector_id: str) -> VectorWriteResponse:
        idx = self._find_entry_index(vector_id)
        if idx is None:
            return self._make_response(error=f"Vector with id {vector_id} not found")

        del self.entries[idx]
        self._rebuild_index()
        self._save()
        return self._make_response(vector_id)

    async def add_vectors(self, vectors: list[VectorAdd]) -> list[VectorWriteResponse]:
        responses = []
        for v in vectors:
            if self._find_entry_index(v.ids) is not None:
                responses.append(self._make_response(error=f"Vector with id {v.ids} already exists"))
                continue
            self.entries.append({
                "id": v.ids,
                "vector": v.vector,
                "metadata": v.metadata
            })
            responses.append(self._make_response(v.ids))
        self._rebuild_index()
        self._save()
        return responses

    async def update_vectors(self, updates: list[VectorUpdate]) -> list[VectorWriteResponse]:
        responses = []
        for u in updates:
            idx = self._find_entry_index(u.ids)
            if idx is None:
                responses.append(self._make_response(error=f"Vector with id {u.ids} not found"))
                continue
            if u.vector is not None:
                self.entries[idx]["vector"] = u.vector
            if u.metadata is not None:
                self.entries[idx]["metadata"] = u.metadata
            responses.append(self._make_response(u.ids))
        self._rebuild_index()
        self._save()
        return responses

    async def delete_vectors(self, vector_ids: list[str]) -> list[VectorWriteResponse]:
        responses = []
        for vid in vector_ids:
            idx = self._find_entry_index(vid)
            if idx is None:
                responses.append(self._make_response(error=f"Vector with id {vid} not found"))
                continue
            del self.entries[idx]
            responses.append(self._make_response(vid))
        self._rebuild_index()
        self._save()
        return responses
