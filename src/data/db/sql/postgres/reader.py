import sqlparse
from logging import Logger
from sqlalchemy import inspect
from sqlalchemy import text
from sqlalchemy.engine import Connection
from src.data.db.sql.base import ISQLReader
from src.data.db.sql.postgres.client import PostgresAsyncClient


class PostgresReader(ISQLReader):
    READ_TYPES = {"SELECT", "WITH", "SHOW", "DESCRIBE", "EXPLAIN"}

    def __init__(self, client: PostgresAsyncClient, logger: Logger | None = None):
        self._client = client
        self.logger = logger or client.logger

    @staticmethod
    def _validate_read_only_query(query: str) -> None:
        parsed = sqlparse.parse(query)
        if not parsed:
            raise ValueError("Empty query")
        for stmt in parsed:
            if stmt.get_type() not in PostgresReader.READ_TYPES:
                raise ValueError(f"Read-only query expected, got: {stmt.get_type()}")

    async def execute(self, query: str, params: dict | None = None) -> list[dict]:
        self.logger.debug(f"Executing read query")
        try:
            self._validate_read_only_query(query)
            result = await self._client.execute(text(query), params)
            if result.returns_rows:
                rows = result.fetchall()
                self.logger.debug(f"Query returned {len(rows)} rows")
                return [dict(row._mapping) for row in rows]
            self.logger.debug("Query executed successfully, no rows returned")
            return []

        except Exception as e:
            self.logger.error(f"Read query failed: {e}", exc_info=True)
            raise

    async def get_schema_info(self) -> str:
        def _build_schema(connection: Connection):
            inspector = inspect(connection)
            tables = inspector.get_table_names()
            if not tables:
                return "No tables found in the database."

            lines = [f"Database has {len(tables)} tables."]
            for table_name in tables:
                cols = []
                for col in inspector.get_columns(table_name):
                    col_name = col["name"]
                    col_type = str(col["type"])
                    nullable = col["nullable"]
                    cols.append(f"{col_name}: {col_type}{' NOT NULL' if not nullable else ''}")
                pk = inspector.get_pk_constraint(table_name)
                primary_keys = pk.get("constrained_columns", [])
                fks = []
                for fk in inspector.get_foreign_keys(table_name):
                    fk_str = f"{fk['name']}:{fk['constrained_columns'][0]}->{fk['referred_table']}.{fk['referred_columns'][0]}"
                    fks.append(fk_str)

                lines.append(f"\nTable: {table_name}")
                if cols:
                    lines.append(f"  Columns: {', '.join(cols)}")
                else:
                    lines.append("  Columns: (none)")
                if primary_keys:
                    lines.append(f"  Primary key: {', '.join(primary_keys)}")
                if fks:
                    lines.append(f"  Foreign keys: {', '.join(fks)}")
            return "\n".join(lines)

        try:
            self.logger.debug("Getting schema info...")
            schema_str = await self._client.run_sync_on_connection(_build_schema)
            self.logger.debug("Schema info retrieved successfully")
            return schema_str
        except Exception as e:
            self.logger.error(f"Failed to get schema info: {e}", exc_info=True)
            raise

    async def connect(self) -> None:
        await self._client.connect()

    async def close(self) -> None:
        await self._client.close()

    async def ping(self) -> bool:
        return await self._client.ping()

    async def begin_transaction(self) -> None:
        await self._client.begin_transaction()

    async def commit_transaction(self) -> None:
        await self._client.commit_transaction()

    async def rollback_transaction(self) -> None:
        await self._client.rollback_transaction()
