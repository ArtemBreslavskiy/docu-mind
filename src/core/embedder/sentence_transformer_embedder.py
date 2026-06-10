from sentence_transformers import SentenceTransformer
from src.core.embedder.base import BaseEmbedder
from src.config.schemas import EmbeddingModelConfig


class SentenceTransformerEmbedder(BaseEmbedder):
    def __init__(self, config: EmbeddingModelConfig):
        self.model = SentenceTransformer(config.name, device=config.device)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()
