from src.retrieval.embedder.base import BaseEmbedder
from src.config.schemas.app.embedder import BaseEmbedderConfig


def create_embedder(config: BaseEmbedderConfig) -> BaseEmbedder:
    embedder_params = config.model_dump(exclude={"type"})

    if config.type == "sentence_transformer":
        from src.retrieval.embedder.sentence_transformer_embedder import SentenceTransformerEmbedder
        return SentenceTransformerEmbedder(**embedder_params)
    else:
        raise ValueError(f"Unknown embedder type: {config.type}")
