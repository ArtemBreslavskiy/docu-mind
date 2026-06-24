from embedders.base import BaseEmbedder
from configs.schemas.pipeline.embedder import BaseEmbedderConfig


def create_embedder(config: BaseEmbedderConfig) -> BaseEmbedder | None:
    if config.type == "disabled":
        return None

    elif config.type == "sentence_transformer":
        from embedders.implementations.sentence_transformer_embedder import SentenceTransformerEmbedder
        embedder_params = config.model_dump(exclude={"type"})
        return SentenceTransformerEmbedder(**embedder_params)

    else:
        raise ValueError(f"Unknown embedder type: {config.type}")
