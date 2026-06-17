from sentence_transformers import SentenceTransformer
from src.core.embedder.base import BaseEmbedder
from src.config.schemas.app import EmbeddingModelConfig


class SentenceTransformerEmbedder(BaseEmbedder):
    def __init__(self, config: EmbeddingModelConfig):
        self.model = SentenceTransformer(config.name, device=config.device)

    def embed(self, texts: list[str], show_progress_bar: bool = True) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=show_progress_bar).tolist()
