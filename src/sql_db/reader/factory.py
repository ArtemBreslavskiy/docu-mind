import os
from src.sql_db.reader.base import BaseSQLReader
from configs.schemas.pipeline.sql_db import BaseSQLDatabaseConfig


def create_sql_reader(config: BaseSQLDatabaseConfig) -> BaseSQLReader | None:
    if config.type == "disabled" or not config.reader.enable:
        return None

    elif config.type == "postgres":
        from src.sql_db.reader.implementations.postgres_reader import PostgresReader

        url = os.getenv(config.env_key, None)
        if not url:
            raise ValueError(f"{config.env_key} environment variable is required for database connection")

        reader_params = config.reader.model_dump(exclude={"enable", "env_key"})
        return PostgresReader(url=url, **reader_params)

    else:
        raise ValueError(f"Unknown sql database type: {config.type}")
