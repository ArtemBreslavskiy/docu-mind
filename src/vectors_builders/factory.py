import logging
from src.vectors_builders.base import BaseVectorsBuilder
from src.configs.schemas.pipeline.vectors_builder import BaseVectorsBuilderConfig
from src.vector_stores.factory import create_vector_store
from src.embedders.factory import create_embedder


def create_vectors_builder(config: BaseVectorsBuilderConfig, logger: logging.Logger) -> BaseVectorsBuilder | None:
    if config.type == "disabled":
        return None

    elif config.type == "default":
        from vectors_builders.implementations.default_vectors_builder import DefaultVectorsBuilder

        vector_store = create_vector_store(config.vector_store)
        if not vector_store:
            raise ValueError("Vector store cannot be disabled")

        embedder = create_embedder(config.embedder)
        if not embedder:
            raise ValueError("Embedder cannot be disabled")

        vectors_builder_params = config.model_dump(exclude={"type", "vector_store", "embedder"})
        return DefaultVectorsBuilder(
            embedder=embedder,
            vector_store=vector_store,
            logger=logger,
            **vectors_builder_params
        )

    else:
        raise ValueError(f"Unknown vectors builder type: {config.type}")
