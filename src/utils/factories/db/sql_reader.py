import os
from data.db.sql.reader.base import BaseSQLReader
from configs.schemas.pipeline.sql_reader import BaseSQLReaderConfig


def create_sql_reader(config: BaseSQLReaderConfig) -> BaseSQLReader | None:
    if config.type == "disabled":
        return None

    elif config.type == "postgres":
        from data.db.sql.postgres.reader import PostgresReader

        url = os.getenv(config.env_key, None)
        if not url:
            raise ValueError(f"{config.env_key} environment variable is required for database connection")

        reader_params = config.reader.model_dump(exclude={"type", "env_key"})
        return PostgresReader(url=url, **reader_params)

    else:
        raise ValueError(f"Unknown sql reader type: {config.type}")
