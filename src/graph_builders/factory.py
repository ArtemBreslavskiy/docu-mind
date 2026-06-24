import logging
from src.graph_builders.base import BaseGraphBuilder
from src.configs.schemas.pipeline.vectors_builder import BaseVectorsBuilderConfig
from src.graph_stores.factory import create_graph_store
from src.embedders.factory import create_embedder
from src.llm.factory import create_llm


def create_graph_builder(config: BaseVectorsBuilderConfig, logger: logging.Logger) -> BaseGraphBuilder | None:
    if config.type == "disabled":
        return None

    elif config.type == "llm_based":
        from graph_builders.implementations.llm_based_graph_builder import LLMBasedGraphBuilder

        graph_store = create_graph_store(config.vector_store)
        if not graph_store:
            raise ValueError("Graph store cannot be disabled")

        llm = create_llm(config.llm)
        if not llm:
            raise ValueError("LLM cannot be disabled")

        embedder = create_embedder(config.embedder)
        if not embedder:
            raise ValueError("Embedder cannot be disabled")

        graph_builder_params = config.model_dump(exclude={"type", "graph_store", "llm", "embedder"})
        return LLMBasedGraphBuilder(
            graph_store=graph_store,
            llm=llm,
            embedder=embedder,
            logger=logger,
            **graph_builder_params
        )

    else:
        raise ValueError(f"Unknown graph builder type: {config.type}")
