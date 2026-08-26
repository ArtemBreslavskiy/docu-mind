import os
from data.db.nosql.reader.base import BaseNoSQLReader
from configs.schemas.pipeline.nosql_reader import BaseNoSQLReaderConfig
from paths.project_paths import ProjectPaths


def create_nosql_reader(config: BaseNoSQLReaderConfig) -> BaseNoSQLReader | None:
    if config.type == "disabled":
        return None

    elif config.type == "faiss":
        from data.db.nosql.vector.faiss.reader import FAISSReader

        path = ProjectPaths()
        reader_params = config.reader.model_dump(exclude={"type"})
        return FAISSReader(log_dir=path.PROCESSED, **reader_params)

    elif config.type == "neo4j":
        from data.db.nosql.graph.neo4j.reader import Neo4jReader

        url = os.getenv(config.env_key, None)
        if not url:
            raise ValueError(f"{config.env_key} environment variable is required for database connection")

        reader_params = config.reader.model_dump(exclude={"type", "env_key"})
        return Neo4jReader(url=url, **reader_params)

    else:
        raise ValueError(f"Unknown graph reader type: {config.type}")
