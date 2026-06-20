from src.retrieval.embedders.base import BaseEmbedder
from config.schemas.pipeline.embedder import BaseEmbedderConfig, SentenceTransformerEmbedderConfig


def create_embedder(config: BaseEmbedderConfig) -> BaseEmbedder:
    if config.type == "sentence_transformer" and isinstance(config, SentenceTransformerEmbedderConfig):
        from src.retrieval.embedders.sentence_transformer_embedder import SentenceTransformerEmbedder
        embedder_params = config.model_dump(exclude={"type"})
        return SentenceTransformerEmbedder(**embedder_params)

    else:
        raise ValueError(f"Unknown embedder type: {config.type}")
