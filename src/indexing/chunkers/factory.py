from indexing.chunkers.base import BaseChunker
from config.schemas.pipeline.chunker import BaseChunkerConfig


def create_chunker(config: BaseChunkerConfig) -> BaseChunker:
    chunker_params = config.model_dump(exclude={"type"})

    if config.type == "recursive":
        from indexing.chunkers.recursive_chunker import RecursiveChunker
        return RecursiveChunker(config=config, **chunker_params)
    else:
        raise ValueError(f"Unknown chunker type: {config.type}")
