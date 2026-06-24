import os
from src.graph_stores.base import BaseGraphStore
from src.configs.schemas.pipeline.graph_store import BaseGraphStoreConfig


def create_graph_store(config: BaseGraphStoreConfig) -> BaseGraphStore | None:
    if config.type == "disabled":
        return None

    elif config.type == "neo4j":
        from graph_stores.implementations.neo4j_store import Neo4jGraphStore

        url = os.getenv("GRAPH_URL", None)
        if not url:
            raise ValueError("GRAPH_URI environment variable is required for Neo4j connection")

        graph_store_params = config.model_dump(exclude={"type"})
        return Neo4jGraphStore(url=url, **graph_store_params)

    else:
        raise ValueError(f"Unknown graph store type: {config.type}")
