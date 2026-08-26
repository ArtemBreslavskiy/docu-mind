import src.data.db_adapters.base as base
from typing import Any
from data.db.nosql.graph.neo4j.reader import Neo4jReader


class Neo4jAdapter(
    base.BaseAdapter,
    base.SearchTextCallable,
    base.GetDistinctValuesCallable,
    base.CountRecordsCallable,
    base.ReadQueryExecutor,
    base.GetSchemaInfoCallable,
):
    def __init__(self, reader: Neo4jReader):
        self.reader = reader

    async def execute_read_query(self, query: Any, params: dict | None = None) -> list[dict]:
        return await self.reader.execute_read(query, params)

    async def get_schema_info(self) -> str:
        return await self.reader.get_schema_info()

    async def search_text(self, table: str, field: str, query: str, limit: int = 10) -> list[dict]:
        cypher = f"""
        MATCH (n:{table})
        WHERE n.{field} CONTAINS $query
        RETURN n
        LIMIT $limit
        """
        return await self.execute_read_query(cypher, {"query": query, "limit": limit})

    async def get_distinct_values(self, table: str, field: str, limit: int = 20) -> list[Any]:
        cypher = f"""
        MATCH (n:{table})
        RETURN DISTINCT n.{field} as value
        LIMIT $limit
        """
        rows = await self.execute_read_query(cypher, {"limit": limit})
        return [row["value"] for row in rows if "value" in row]

    async def count_records(self, table: str, filter: dict | None = None) -> int:
        params = {}
        where_clause = ""
        if filter:
            conditions = " AND ".join(f"n.{k} = ${k}" for k in filter.keys())
            where_clause = f"WHERE {conditions}"
            params = filter
        cypher = f"""
        MATCH (n:{table})
        {where_clause}
        RETURN count(n) as count
        """
        rows = await self.execute_read_query(cypher, params)
        return rows[0]["count"] if rows else 0
