from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from src.sql_db.writer.base import BaseSQLWriter
from typing import Any


class PostgresWriter(BaseSQLWriter):
    def __init__(self, url: str, **kwargs):
        super().__init__(**kwargs)
        self.engine = create_async_engine(url, echo=False, pool_pre_ping=True)

    async def _execute(self, query: str, params: dict | None = None) -> int:
        async with self.engine.connect() as conn:
            result = await conn.execute(text(query), params or {})
            await conn.commit()
            return result.rowcount

    async def insert_one(self, table: str, data: dict[str, Any]) -> Any:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data.keys())
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        rowcount = await self._execute(query, data)
        return rowcount

    async def update_one(self, table: str, filter: dict[str, Any], update_data: dict[str, Any]) -> int:
        set_clause = ", ".join(f"{k} = :{k}" for k in update_data.keys())
        where_clause = " AND ".join(f"{k} = :{k}_filter" for k in filter.keys())
        params = {**update_data, **{f"{k}_filter": v for k, v in filter.items()}}
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        return await self._execute(query, params)

    async def delete_one(self, table: str, filter: dict[str, Any]) -> int:
        where_clause = " AND ".join(f"{k} = :{k}" for k in filter.keys())
        query = f"DELETE FROM {table} WHERE {where_clause}"
        return await self._execute(query, filter)

    async def insert_many(self, table: str, data_list: list[dict[str, Any]]) -> int:
        if not data_list:
            return 0
        columns = ", ".join(data_list[0].keys())
        placeholders = ", ".join(f":{k}" for k in data_list[0].keys())
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        total = 0
        async with self.engine.connect() as conn:
            for data in data_list:
                result = await conn.execute(text(query), data)
                total += result.rowcount
            await conn.commit()
        return total

    async def update_many(self, table: str, filter: dict[str, Any], update_data: dict[str, Any]) -> int:
        return await self.update_one(table, filter, update_data)

    async def delete_many(self, table: str, filter: dict[str, Any]) -> int:
        return await self.delete_one(table, filter)

    async def close(self) -> None:
        if self.engine:
            await self.engine.dispose()
            self.engine = None