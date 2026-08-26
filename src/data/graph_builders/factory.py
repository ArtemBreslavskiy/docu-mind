import logging
from data.graph_builders.base import BaseGraphBuilder
from configs.schemas.pipeline.graph.builder import BaseGraphBuilderConfig
from src.graph_stores.factory import create_graph_store
from utils.factories.embedders import create_embedder
from utils.factories.llm import create_llm


def create_graph_builder(config: BaseGraphBuilderConfig, logger: logging.Logger) -> BaseGraphBuilder | None:
    if config.type == "disabled":
        return None

    elif config.type == "llm_based":
        from data.graph_builders.implementations.llm_based_graph_builder import LLMBasedGraphBuilder

        graph_store = create_graph_store(config.graph_store)
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
