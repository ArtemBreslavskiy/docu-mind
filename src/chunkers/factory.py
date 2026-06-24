from chunkers.base import BaseChunker
from configs.schemas.pipeline.chunker import BaseChunkerConfig


def create_chunker(config: BaseChunkerConfig) -> BaseChunker | None:
    if config.type == "disabled":
        return None

    elif config.type == "recursive":
        from chunkers.implementations.recursive_chunker import RecursiveChunker
        chunker_params = config.model_dump(exclude={"type"})
        return RecursiveChunker(config=config, **chunker_params)

    else:
        raise ValueError(f"Unknown chunker type: {config.type}")
