import logging
import math
import json
import time
from tqdm import tqdm
from src.core_schemas import Chunk
from src.graph_builders.base import BaseGraphBuilder
from src.graph_stores.base import BaseGraphStore
from src.embedders.base import BaseEmbedder
from langchain_core.language_models.chat_models import BaseChatModel
from src.logger.logger_setup import get_logger


class LLMBasedGraphBuilder(BaseGraphBuilder):
    def __init__(
        self,
        graph_store: BaseGraphStore,
        llm: BaseChatModel,
        embedder: BaseEmbedder,
        batch_size: int = 10,
        similarity_threshold: float = 0.85,
        logger: logging.Logger = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.graph_store = graph_store
        self.llm = llm
        self.embedder = embedder
        self.batch_size = batch_size
        self.similarity_threshold = similarity_threshold
        self.logger = logger if logger is not None else get_logger("pipeline")
        if logger is None:
            self.logger.disabled = True

    def build(self, chunks: list[Chunk], show_progress_bar: bool = True) -> None:
        self.logger.info("Starting full graph build from %d chunks...", len(chunks))
        start_time = time.perf_counter()
        self._clear_graph()
        self._add_documents(chunks, show_progress_bar)
        self.logger.info("Graph build completed in %.2f sec", time.perf_counter() - start_time)

    def add_documents(self, chunks: list[Chunk], show_progress_bar: bool = True) -> None:
        self.logger.info("Adding %d chunks to graph...", len(chunks))
        self._add_documents(chunks, show_progress_bar)

    def _add_documents(self, chunks: list[Chunk], show_progress_bar: bool) -> None:
        total_chunks = len(chunks)
        total_batches = (total_chunks + self.batch_size - 1) // self.batch_size
        batch_indices = range(0, total_chunks, self.batch_size)

        if show_progress_bar:
            batch_indices = tqdm(
                batch_indices,
                desc="Building graph",
                total=total_batches,
                unit="batch"
            )

        for i in batch_indices:
            batch = chunks[i:i + self.batch_size]
            self.logger.debug("Processing batch %d-%d of %d", i, min(i + self.batch_size, total_chunks), total_chunks)
            self._process_batch(batch)

            if show_progress_bar:
                batch_indices.set_postfix({
                    "chunks": min(i + self.batch_size, total_chunks),
                    "total": total_chunks
                })

    def _clear_graph(self) -> None:
        self.logger.info("Clearing graph...")
        try:
            self.graph_store.query("MATCH (n:Entity) DETACH DELETE n")
        except Exception as e:
            self.logger.error("Failed to clear graph: %s", e)
            raise
        self.logger.info("Graph cleared.")

    def _process_batch(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return

        triples = self._extract_triples_from_chunks(chunks)
        if not triples:
            self.logger.warning("No triples extracted from batch")
            return

        for subj, rel, obj in triples:
            self._add_triple(subj, rel, obj)

    def _extract_triples_from_chunks(self, chunks: list[Chunk]) -> list[tuple[str, str, str]]:
        texts = [chunk.content for chunk in chunks]
        combined_text = "\n---\n".join(texts)

        system_prompt = (
            "You are an assistant that extracts entities and relationships from text.\n"
            "Return ONLY a JSON list of triples in the format:\n"
            '[{"subject": "...", "relation": "...", "object": "..."}]\n'
            "Do not include any other text or explanation."
        )
        user_prompt = f"Extract triples from the following text:\n\n{combined_text}"

        try:
            response = self.llm.invoke(system_prompt + "\n\n" + user_prompt)
            triples = self._parse_llm_response(response)
            self.logger.debug("Extracted %d triples from batch", len(triples))
            return triples
        except Exception as e:
            self.logger.error("LLM extraction failed: %s", e)
            return []

    def _parse_llm_response(self, response: str) -> list[tuple[str, str, str]]:
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines)

            data = json.loads(cleaned)
            triples = []
            for item in data:
                if isinstance(item, dict) and "subject" in item and "relation" in item and "object" in item:
                    triples.append((item["subject"], item["relation"], item["object"]))
            return triples
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse JSON from LLM response: %s", e)
            self.logger.debug("Response was: %s", response)
            return []
        except Exception as e:
            self.logger.error("Unexpected error parsing LLM response: %s", e)
            return []

    def _add_triple(self, subj: str, rel: str, obj: str) -> None:
        subj_id = self._get_or_create_node(subj)
        obj_id = self._get_or_create_node(obj)
        if subj_id and obj_id:
            self.graph_store.create_relationship(subj_id, obj_id, rel.upper(), {})
        else:
            self.logger.warning("Failed to create relationship %s -> %s", subj, obj)

    def _get_or_create_node(self, name: str) -> str | None:
        result = self.graph_store.query(
            "MATCH (n:Entity {name: $name}) RETURN id(n) as id",
            {"name": name}
        )
        if result:
            return str(result[0]["id"])

        props = {"name": name}
        if self.embedder:
            name_emb = self.embedder.embed([name])[0]
            props["embedding"] = name_emb

            all_nodes = self.graph_store.query(
                "MATCH (n:Entity) WHERE n.embedding IS NOT NULL RETURN n.name as name, n.embedding as emb"
            )

            for node in all_nodes:
                sim = self._cosine_similarity(name_emb, node["emb"])
                if sim > self.similarity_threshold:
                    self.logger.debug("Merging '%s' with existing '%s' (sim=%.3f)", name, node["name"], sim)
                    return self._get_node_id_by_name(node["name"])
        return self.graph_store.create_node("Entity", props)

    def _get_node_id_by_name(self, name: str) -> str | None:
        result = self.graph_store.query(
            "MATCH (n:Entity {name: $name}) RETURN id(n) as id",
            {"name": name}
        )
        return str(result[0]["id"]) if result else None

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)
