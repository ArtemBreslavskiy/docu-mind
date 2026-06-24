from src.graph_builders.base import BaseGraphBuilder
from src.configs.schemas.pipeline.vectors_builder import BaseVectorsBuilderConfig
from src.graph_stores.factory import create_graph_store
from src.embedders.factory import create_embedder
from src.llm.factory import create_llm
from src.logger.logger_setup import get_logger


def create_graph_builder(config: BaseVectorsBuilderConfig) -> BaseGraphBuilder | None:
    if config.type == "disabled":
        return None

    elif config.type == "llm_based":
        from graph_builders.implementations.llm_based_graph_builder import LLMBasedGraphBuilder

        graph_store = create_graph_store(config.vector_store)
        embedder = create_embedder(config.embedder)
        llm = create_llm(config.llm)
        logger = get_logger("pipeline")
        graph_builder_params = config.model_dump(exclude={"type", "graph_store", "embedder", "llm"})

        return LLMBasedGraphBuilder(
            graph_store=graph_store,
            embedder=embedder,
            logger=logger,
            **graph_builder_params
        )

    else:
        raise ValueError(f"Unknown graph builder type: {config.type}")
