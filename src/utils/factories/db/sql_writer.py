import os
from data.db.sql.base import BaseSQLWriter
from configs.schemas.pipeline.sql_writer import BaseSQLWriterConfig


def create_sql_writer(config: BaseSQLWriterConfig) -> BaseSQLWriter | None:
    if config.type == "disabled":
        return None

    elif config.type == "postgres":
        from data.db.sql.postgres.writer import PostgresWriter

        url = os.getenv(config.env_key, None)
        if not url:
            raise ValueError(f"{config.env_key} environment variable is required for database connection")

        writer_params = config.writer.model_dump(exclude={"type", "env_key"})
        return PostgresWriter(url=url, **writer_params)

    else:
        raise ValueError(f"Unknown sql writer type: {config.type}")
