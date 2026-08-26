import src.data.db_adapters.base as base
from data.db.sql.postgres.reader import PostgresReader
from typing import Any


class PostgresAdapter(
    base.BaseAdapter,
    base.SearchTextCallable,
    base.GetDistinctValuesCallable,
    base.CountRecordsCallable,
    base.ReadQueryExecutor,
    base.GetSchemaInfoCallable,
):
    def __init__(self, reader: PostgresReader):
        self.reader = reader

    async def execute_read_query(self, query: Any, params: dict | None = None) -> list[dict]:
        return await self.reader.select(query, params or {})

    async def get_schema_info(self) -> str:
        return await self.reader.get_schema_info()

    async def search_text(self, table: str, field: str, query: str, limit: int = 10) -> list[dict]:
        sql = f"SELECT * FROM {table} WHERE {field} ILIKE %(query)s LIMIT %(limit)s"
        params = {"query": f"%{query}%", "limit": limit}
        return await self.reader.select(sql, params)

    async def get_distinct_values(self, table: str, field: str, limit: int = 20) -> list[Any]:
        sql = f"SELECT DISTINCT {field} FROM {table} LIMIT %(limit)s"
        rows = await self.reader.select(sql, {"limit": limit})
        return [row[field] for row in rows]

    async def count_records(self, table: str, filter: dict | None = None) -> int:
        sql = f"SELECT COUNT(*) as count FROM {table}"
        params = {}
        if filter:
            conditions = " AND ".join(f"{k} = %({k})s" for k in filter.keys())
            sql += f" WHERE {conditions}"
            params = filter
        rows = await self.reader.select(sql, params)
        return rows[0]["count"] if rows else 0
