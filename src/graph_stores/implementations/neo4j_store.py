from neo4j import GraphDatabase, Query
from src.graph_stores.base import BaseGraphStore
from typing import Any


class Neo4jGraphStore(BaseGraphStore):
    def __init__(self, url: str, **kwargs):
        super().__init__(**kwargs)
        self.driver = GraphDatabase.driver(url)

    def query(self, query: str, parameters: dict[str, Any] = None) -> list[dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(Query(query), parameters or {})
            return [record.data() for record in result]

    def create_node(self, label: str, properties: dict[str, Any]) -> str:
        query = f"CREATE (n:{label} $props) RETURN id(n) as id"
        with self.driver.session() as session:
            result = session.run(Query(query), props=properties)
            return str(result.single()["id"])

    def create_relationship(self, from_node_id: str, to_node_id: str, rel_type: str, properties: dict[str, Any] = None):
        query = (
            f"MATCH (a), (b) WHERE id(a) = $from_id AND id(b) = $to_id "
            f"CREATE (a)-[:{rel_type} $props]->(b)"
        )
        with self.driver.session() as session:
            session.run(Query(query), from_id=int(from_node_id), to_id=int(to_node_id), props=properties or {})

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        query = "MATCH (n) WHERE id(n) = $id RETURN n"
        with self.driver.session() as session:
            result = session.run(Query(query), id=int(node_id))
            record = result.single()
            if record:
                return dict(record["n"])
            return None

    def close(self) -> None:
        if self.driver:
            self.driver.close()
            self.driver = None
