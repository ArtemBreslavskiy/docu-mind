from sqlalchemy import inspect
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from src.sql_db.reader.base import BaseSQLReader


class PostgresReader(BaseSQLReader):
    def __init__(self, url: str, **kwargs):
        super().__init__(**kwargs)
        self.engine = create_async_engine(url, echo=False, pool_pre_ping=True)
        
    async def select(
        self, query: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        if not query.strip().lower().startswith("select"):
            raise ValueError("Only SELECT queries are allowed in read-only mode")
        async with self.engine.connect() as conn:
            stmt = text(query)
            result = await conn.execute(stmt, params or {})
            rows = result.fetchall()
            columns = list(result.keys())
            return [dict(zip(columns, row)) for row in rows]

    async def get_schema_info(self) -> dict[str, Any]:
        schema_info = {"tables": {}}
        async with self.engine.connect() as conn:
            inspector = inspect(self.engine)
            tables = await inspector.get_table_names()
            for table_name in tables:
                columns_info = {}
                for col in await inspector.get_columns(table_name):
                    columns_info[col["name"]] = {
                        "type": str(col["type"]),
                        "nullable": col["nullable"],
                        "default": col.get("default"),
                        "primary_key": col.get("primary_key", False)
                    }
                pk = await inspector.get_pk_constraint(table_name)
                primary_keys = pk.get("constrained_columns", [])
                foreign_keys = []
                for fk in await inspector.get_foreign_keys(table_name):
                    fk_str = f"{fk['name']}:{fk['constrained_columns'][0]}->{fk['referred_table']}.{fk['referred_columns'][0]}"
                    foreign_keys.append(fk_str)
                schema_info["tables"][table_name] = {
                    "columns": columns_info,
                    "primary_key": primary_keys,
                    "foreign_keys": foreign_keys
                }
        return schema_info

    async def close(self) -> None:
        if self.engine:
            await self.engine.dispose()
            self.engine = None
