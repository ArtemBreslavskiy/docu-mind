from src.data.chunkers.base import BaseChunker
from src.data.chunkers.recursive_chunker import RecursiveChunker
from src.config.schemas.pipeline import ChunkerConfig


def create_chunker(config: ChunkerConfig) -> BaseChunker:
    if config.type == "recursive":
        return RecursiveChunker(config=config)
    else:
        raise ValueError(f"Unknown chunker type: {config.type}")
