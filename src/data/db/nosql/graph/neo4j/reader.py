from logging import Logger
from typing import Any
from antlr4 import InputStream, CommonTokenStream
from antlr4_cypher import CypherLexer, CypherParser
from data.db.nosql.graph.base import BaseGraphReader
from data.db.nosql.graph.neo4j.client import Neo4jAsyncClient


class Neo4jReader(BaseGraphReader):
    READ_RULE_NAMES = {
        "script",
        "statement",
        "query",
        "regularQuery",
        "singleQuery",
        "clauses",
        "matchSt",
        "optionalMatch",
        "returnSt",
        "withSt",
        "unwindSt",
        "whereSt",
        "orderBySt",
        "skipSt",
        "limitSt",
        "callSt",
        "unionSt",
        "useSt",
    }

    def __init__(self, client: Neo4jAsyncClient, logger: Logger, **kwargs):
        super().__init__(**kwargs)
        self._client = client
        self.logger = logger or client.logger

    @staticmethod
    def _validate_read_query(query: str) -> None:
        def walk(ctx):
            rule_name = parser.ruleNames[ctx.getRuleIndex()]
            if rule_name not in Neo4jReader.READ_RULE_NAMES:
                raise ValueError(f"Operation '{rule_name}' not allowed in read-only query")
            for child in ctx.getChildren():
                if hasattr(child, "getRuleIndex"):
                    walk(child)

        input_stream = InputStream(query)
        lexer = CypherLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = CypherParser(stream)
        tree = parser.script()
        walk(tree)

    async def read_query(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        self.logger.debug(f"Executing read query")
        try:
            self._validate_read_query(query)
            result = await self._client.execute(query, params)
            if result:
                self.logger.debug(f"Query returned {len(result)} rows")
            else:
                self.logger.debug("Query executed successfully, no rows returned")
            return result

        except Exception as e:
            self.logger.error(f"Read query failed: {e}", exc_info=True)
            raise

    async def get_schema_info(self) -> str:
        node_count = await self._client.execute("MATCH (n) RETURN count(n) as count")
        total_nodes = node_count[0]["count"] if node_count else 0

        rel_count = await self._client.execute("MATCH ()-[r]->() RETURN count(r) as count")
        total_rels = rel_count[0]["count"] if rel_count else 0

        labels_result = await self._client.execute("CALL db.labels()")
        labels = [record["label"] for record in labels_result]

        rel_types_result = await self._client.execute("CALL db.relationshipTypes()")
        rel_types = [record["relationshipType"] for record in rel_types_result]

        lines = [
            f"Graph has {total_nodes} nodes and {total_rels} relationships.",
            f"Node labels (sample): {', '.join(labels)}." if labels else "No node labels found.",
            f"Relationship types (sample): {', '.join(rel_types)}." if rel_types else "No relationship types found.",
        ]
        return "\n".join(lines)

    async def close(self) -> None:
        self.logger.debug("Closing Neo4jReader client")
        await self._client.close()
        self.logger.debug("Neo4jReader client closed")
