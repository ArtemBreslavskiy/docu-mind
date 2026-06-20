from sentence_transformers import SentenceTransformer
from retrieval.embedders.base import BaseEmbedder


class SentenceTransformerEmbedder(BaseEmbedder):
    def __init__(self, name: str, device: str, **kwargs):
        super().__init__(**kwargs)
        self.model = SentenceTransformer(name=name, device=device)

    def embed(self, texts: list[str], show_progress_bar: bool = True) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=show_progress_bar).tolist()
