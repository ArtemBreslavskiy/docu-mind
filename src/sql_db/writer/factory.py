import os
from src.sql_db.writer.base import BaseSQLWriter
from configs.schemas.pipeline.sql_db import BaseSQLDatabaseConfig


def create_sql_writer(config: BaseSQLDatabaseConfig) -> BaseSQLWriter | None:
    if config.type == "disabled" or not config.writer.enable:
        return None

    elif config.type == "postgres":
        from src.sql_db.writer.implementations.postgres_writer import PostgresWriter

        url = os.getenv(config.env_key, None)
        if not url:
            raise ValueError(f"{config.env_key} environment variable is required for database connection")

        writer_params = config.writer.model_dump(exclude={"enable", "env_key"})
        return PostgresWriter(url=url, **writer_params)

    else:
        raise ValueError(f"Unknown sql database type: {config.type}")
