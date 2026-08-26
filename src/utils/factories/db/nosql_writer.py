import os
from data.db.base import BaseNoSQLWriter
from configs.schemas.pipeline.nosql_writer import BaseNoSQLWriterConfig
from paths.project_paths import ProjectPaths


def create_graph_writer(config: BaseNoSQLWriterConfig) -> BaseNoSQLWriter | None:
    if config.type == "disabled":
        return None

    elif config.type == "faiss":
        from data.db.nosql.vector.faiss.writer import FAISSWriter

        path = ProjectPaths()
        reader_params = config.reader.model_dump(exclude={"type"})
        return FAISSWriter(log_dir=path.PROCESSED, **reader_params)

    elif config.type == "neo4j":
        from data.db.nosql.graph.neo4j.writer import Neo4jWriter

        url = os.getenv(config.env_key, None)
        if not url:
            raise ValueError(f"{config.env_key} environment variable is required for database connection")

        reader_params = config.reader.model_dump(exclude={"type", "env_key"})
        return Neo4jWriter(url=url, **reader_params)

    else:
        raise ValueError(f"Unknown graph writer type: {config.type}")
