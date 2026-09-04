from typing import Any
from functools import partial
from logging import Logger
from antlr4 import InputStream, CommonTokenStream
from antlr4_cypher import CypherLexer, CypherParser
from data.db.filter import FilterCondition, FilterGroup
from src.data.db.nosql.graph.neo4j.client import Neo4jAsyncClient
from src.data.db.nosql.graph.base import (
    IGraphWriter,
    NodeCreate,
    NodeUpdate,
    RelationshipCreate,
    RelationshipUpdate,
)
from src.utils.truncate import truncate
from src.utils.neo4j_utils import escape_identifier, convert_filter
from src.utils.db_utils import (
    validate_strings_exist,
    validate_dict_exist,
    validate_dict_contains_consistent_keys,
    validate_all_conflict_properties_in_properties,
    validate_match_not_contains_duplicates,
    validate_filter_exist
)


class Neo4jWriter(IGraphWriter):
    WRITE_RULE_NAMES = {
        "createSt",
        "mergeSt",
        "deleteSt",
        "setSt",
        "removeSt",
        "createIndex",
        "dropIndex",
        "createConstraint",
        "dropConstraint",
        "createUniqueConstraint",
        "dropUniqueConstraint",
    }
    ALLOWED_FILTER_OPS = {"gt", "lt", "gte", "lte", "ne", "in", "isnull", "like", "ilike"}
    MAX_VALIDATION_ERRORS = 20
    MAX_LABEL_LENGTH = 500
    MAX_REL_TYPE_LENGTH = 500
    MAX_PROPERTIES_LENGTH = 500
    MAX_CONFLICT_PROPERTIES_LENGTH = 500
    MAX_MATCH_LENGTH = 500
    MAX_FILTER_LENGTH = 500
    MAX_QUERY_LENGTH = 500

    def __init__(self, client: Neo4jAsyncClient, logger: Logger, **kwargs):
        super().__init__(**kwargs)
        self._client = client
        self.logger = logger or client.logger

    @staticmethod
    def _validate_strings_exist(strings: str | list[str], context: str = "") -> str | None:
        return validate_strings_exist(strings, context, Neo4jWriter.MAX_VALIDATION_ERRORS, True)

    @staticmethod
    def _validate_dict_exist(data: dict | list[dict], context: str = "") -> str | None:
        return validate_dict_exist(data, context, Neo4jWriter.MAX_VALIDATION_ERRORS, True)

    @staticmethod
    def _validate_dict_contains_consistent_keys(data_list: list[dict], context: str = "") -> str | None:
        return validate_dict_contains_consistent_keys(data_list, context, Neo4jWriter.MAX_VALIDATION_ERRORS, True)

    @staticmethod
    def _validate_all_conflict_properties_in_properties(
        properties: dict | list[dict],
        conflict_properties: list[str]
    ) -> str | None:
        return validate_all_conflict_properties_in_properties(
            properties,
            conflict_properties,
            Neo4jWriter.MAX_VALIDATION_ERRORS,
            True
        )

    @staticmethod
    def _validate_match_not_contains_duplicates(match: list[dict]) -> str | None:
        return validate_match_not_contains_duplicates(match, Neo4jWriter.MAX_VALIDATION_ERRORS, True)

    @staticmethod
    def _validate_filter_exist(filter: FilterCondition | FilterGroup) -> str | None:
        return validate_filter_exist(filter, Neo4jWriter.MAX_VALIDATION_ERRORS, return_str=True)

    @staticmethod
    def _validate_write_query(query: str) -> None:
        def walk(ctx):
            rule_name = parser.ruleNames[ctx.getRuleIndex()]
            if rule_name not in Neo4jWriter.WRITE_RULE_NAMES:
                raise ValueError(f"Operation '{rule_name}' not allowed in write-only query")
            for child in ctx.getChildren():
                if hasattr(child, "getRuleIndex"):
                    walk(child)

        input_stream = InputStream(query)
        lexer = CypherLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = CypherParser(stream)
        tree = parser.script()
        walk(tree)

    @staticmethod
    def _run_validation(checks: list[partial]) -> None:
        error_lines = []
        for check in checks:
            res = check()
            if res:
                error_lines.append(res)
        if len(error_lines) > 1:
            raise ValueError("Validation errors:\n" + "\n".join(error_lines))
        elif len(error_lines) == 1:
            raise ValueError(error_lines[0])

    @staticmethod
    def _validate_labels_partials(labels: str | list[str]) -> list[partial]:
        return [partial(Neo4jWriter._validate_strings_exist, labels, "Labels")]

    @staticmethod
    def _validate_rel_types_partials(rel_types: str | list[str]) -> list[partial]:
        return [partial(Neo4jWriter._validate_strings_exist, rel_types, "Relationship types")]

    @staticmethod
    def _validate_from_ids_partials(from_ids: str | list[str]) -> list[partial]:
        return [partial(Neo4jWriter._validate_strings_exist, from_ids, "From ids")]

    @staticmethod
    def _validate_to_ids_partials(to_ids: str | list[str]) -> list[partial]:
        return [partial(Neo4jWriter._validate_strings_exist, to_ids, "To ids")]

    @staticmethod
    def _validate_conflict_properties_partials(conflict_properties: list[str]) -> list[partial]:
        return [partial(Neo4jWriter._validate_strings_exist, conflict_properties, "Conflict properties")]

    @staticmethod
    def _validate_match_partials(match: dict | list[dict]) -> list[partial]:
        checks = [partial(Neo4jWriter._validate_dict_exist, match, "Match")]
        if isinstance(match, list):
            checks.extend([
                partial(Neo4jWriter._validate_match_not_contains_duplicates, match),
                partial(Neo4jWriter._validate_dict_contains_consistent_keys, match, "Match"),
            ])
        return checks

    @staticmethod
    def _validate_filter_partials(filter: FilterCondition | FilterGroup):
        return [partial(Neo4jWriter._validate_filter_exist, filter)]

    @staticmethod
    def _validate_create_operation(
        labels: str | list[str] | None = None,
        rel_types: str | list[str] | None = None,
        from_ids: Any | list[Any] | None = None,
        to_ids: Any | list[Any] | None = None,
        properties: dict | list[dict] | None = None
    ) -> None:
        checks = []
        if labels:
            checks.extend(Neo4jWriter._validate_labels_partials(labels))
        if rel_types:
            checks.extend(Neo4jWriter._validate_rel_types_partials(rel_types))
        if from_ids:
            checks.extend(Neo4jWriter._validate_from_ids_partials(from_ids))
        if to_ids:
            checks.extend(Neo4jWriter._validate_to_ids_partials(to_ids))
        if properties:
            checks.append([partial(Neo4jWriter._validate_dict_exist, properties, "Properties")])
            if isinstance(properties, list):
                checks.append(partial(
                    Neo4jWriter._validate_dict_contains_consistent_keys,
                    properties,
                    "Properties"
                ))
        if checks:
            Neo4jWriter._run_validation(checks)

    @staticmethod
    def _validate_upsert_operation(
        properties: dict | list[dict],
        conflict_properties: list[str],
        labels: str | list[str] | None = None,
        rel_types: str | list[str] | None = None,
        from_ids: Any | list[Any] | None = None,
        to_ids: Any | list[Any] | None = None,
    ) -> None:
        checks = []
        if labels:
            checks.extend(Neo4jWriter._validate_labels_partials(labels))
        if rel_types:
            checks.extend(Neo4jWriter._validate_rel_types_partials(rel_types))
        if from_ids:
            checks.extend(Neo4jWriter._validate_from_ids_partials(from_ids))
        if to_ids:
            checks.extend(Neo4jWriter._validate_to_ids_partials(to_ids))
        checks.extend([
            partial(Neo4jWriter._validate_dict_exist, properties, "Upsert properties"),
            partial(Neo4jWriter._validate_all_conflict_properties_in_properties, properties, conflict_properties)
        ])
        if isinstance(properties, list):
            checks.append(partial(
                Neo4jWriter._validate_dict_contains_consistent_keys,
                properties,
                "Upsert properties"
            ))
        checks.append(Neo4jWriter._validate_conflict_properties_partials(conflict_properties))
        Neo4jWriter._run_validation(checks)

    @staticmethod
    def _validate_update_operation(
        update_properties: dict | list[dict],
        match: dict | list[dict] | None = None,
        filter: FilterCondition | FilterGroup | None = None,
    ) -> None:
        checks = [partial(Neo4jWriter._validate_dict_exist, update_properties, "Update properties")]
        if isinstance(update_properties, list):
            checks.append(partial(
                Neo4jWriter._validate_dict_contains_consistent_keys,
                update_properties,
                "Update properties")
            )
        if match:
            checks.extend(Neo4jWriter._validate_match_partials(match))
        if filter:
            checks.extend(Neo4jWriter._validate_filter_partials(filter))
        Neo4jWriter._run_validation(checks)

    @staticmethod
    def _validate_delete_operation(
        match: dict | list[dict] | None = None,
        filter: FilterCondition | FilterGroup = None,
    ) -> None:
        checks = []
        if match:
            checks.extend(Neo4jWriter._validate_match_partials(match))
        if filter:
            checks.extend(Neo4jWriter._validate_filter_partials(filter))
        if checks:
            Neo4jWriter._run_validation(checks)

    async def execute(
        self,
        query: str,
        params: dict | list[dict] | None = None
    ) -> list[dict]:
        self.logger.debug(f"Executing raw write query")
        try:
            self._validate_write_query(query)
            result = await self._client.execute(query, params, returning=True)
            self.logger.debug(f"Write query executed successfully, returned {len(result)} records")
            return result

        except Exception as e:
            self.logger.error(f"Write query failed: {e}", exc_info=True)
            raise

    async def create_one_node(self, label: str, properties: dict) -> str:
        self.logger.info(f"Creating one node with label '{label}'")
        self.logger.debug(
            f"label: {truncate(label, Neo4jWriter.MAX_LABEL_LENGTH)}, "
            f"properties: {truncate(str(properties), Neo4jWriter.MAX_PROPERTIES_LENGTH)}"
        )
        try:
            self._validate_create_operation(label, properties=properties)
            query = f"CREATE (n:`{escape_identifier(label)}` $props) RETURN id(n) as id"

            result = await self._client.execute(query, {"props": properties}, returning=True)
            if not result:
                raise RuntimeError("Node create returned no ID")
            node_id = str(result[0]["id"])
            self.logger.info(f"Created node with id={node_id} (label '{label}')")
            return node_id

        except Exception as e:
            self.logger.error(f"Failed to create node with label '{label}': {e}", exc_info=True)
            raise

    async def upsert_one_node(
        self,
        label: str,
        properties: dict,
        conflict_properties: list[str],
    ) -> str:
        self.logger.info(f"Upserting one node with label '{label}'")
        self.logger.debug(
            f"label: {truncate(label, Neo4jWriter.MAX_LABEL_LENGTH)}, "
            f"properties: {truncate(str(properties), Neo4jWriter.MAX_PROPERTIES_LENGTH)}, "
            f"conflict properties: {truncate(str(conflict_properties), Neo4jWriter.MAX_CONFLICT_PROPERTIES_LENGTH)}"
        )
        try:
            self._validate_upsert_operation(label, properties=properties, conflict_properties=conflict_properties)
            conditions = ", ".join(f"`{col}`: ${col}" for col in conflict_properties)
            params = {col: properties[col] for col in conflict_properties}
            params["props"] = {k: v for k, v in properties.items() if k not in conflict_properties}
            query = f"""
                MERGE (n:`{escape_identifier(label)}` {{{conditions}}})
                SET n += $props
                RETURN id(n) as id
                """

            result = await self._client.execute(query, params, returning=True)
            if not result:
                raise RuntimeError("Node upsert returned no ID")
            node_id = str(result[0]["id"])
            self.logger.info(f"Upserted node with id={node_id} (label '{label}')")
            return node_id

        except Exception as e:
            self.logger.error(f"Failed to upsert node with label '{label}': {e}", exc_info=True)
            raise

    async def update_one_node(self, update_properties: dict, match: dict) -> str:
        self.logger.info("Updating one node by match")
        self.logger.debug(
            f"update properties: {truncate(str(update_properties), Neo4jWriter.MAX_PROPERTIES_LENGTH)}, "
            f"match: {truncate(str(match), Neo4jWriter.MAX_MATCH_LENGTH)}"
        )
        try:
            self._validate_update_operation(update_properties, match)
            conditions = []
            params = {}
            for key, value in match.items():
                conditions.append(f"n.`{escape_identifier(key)}` = ${key}")
                params[key] = value
            params["props"] = update_properties
            where_clause = " AND ".join(conditions)

            query = f"""
                MATCH (n)
                WHERE {where_clause}
                SET n += $props
                RETURN id(n) as id
                """

            result = await self._client.execute(query, params, returning=True)
            if not result:
                raise RuntimeError("Node update returned no ID")
            node_id = str(result[0]["id"])
            self.logger.info(f"Updated node with id={node_id}")
            return node_id

        except Exception as e:
            self.logger.error(f"Failed to update node: {e}", exc_info=True)
            raise

    async def delete_one_node(self, match: dict) -> str:
        self.logger.info("Deleting one node by match")
        self.logger.debug(f"match: {truncate(str(match), Neo4jWriter.MAX_MATCH_LENGTH)}")
        try:
            self._validate_delete_operation(match)
            conditions = []
            params = {}
            for key, value in match.items():
                conditions.append(f"n.`{escape_identifier(key)}` = ${key}")
                params[key] = value
            where_clause = " AND ".join(conditions)

            query = f"""
                MATCH (n)
                WHERE {where_clause}
                DETACH DELETE n
                RETURN id(n) as id
                """

            result = await self._client.execute(query, params, returning=True)
            if not result:
                raise RuntimeError("Node delete returned no ID")
            node_id = str(result[0]["id"])
            self.logger.info(f"Deleted node with id={node_id}")
            return node_id

        except Exception as e:
            self.logger.error(f"Failed to delete node: {e}", exc_info=True)
            raise

    async def create_many_nodes(self, nodes: list[NodeCreate]) -> list[str]:
        self.logger.info(f"Creating {len(nodes)} nodes")
        labels = list({node.label for node in nodes})
        self.logger.debug(
            f"labels: {truncate(str(labels), Neo4jWriter.MAX_LABEL_LENGTH)}, "
            f"first node properties: {
                truncate(str(nodes[0].properties) if nodes else '', Neo4jWriter.MAX_PROPERTIES_LENGTH)
            }"
        )
        try:
            properties = [node.properties for node in nodes]
            self._validate_create_operation(labels, properties=properties)

            results = {}
            groups = {}
            for i, node in enumerate(nodes):
                groups.setdefault(node.label, []).append((i, node.properties))

            for label, items in groups.items():
                indices = [i for i, _ in items]
                props_list = [props for _, props in items]

                query = f"""
                    UNWIND $props_list AS props
                    CREATE (n:`{escape_identifier(label)}` props)
                    RETURN id(n) as id
                    """
                params = {"props_list": props_list}

                result = await self._client.execute(query, params, returning=True)
                if len(result) != len(indices):
                    raise RuntimeError(f"Expected {len(indices)} nodes for label '{label}', got {len(result)}")

                for idx, record in zip(indices, result):
                    results[idx] = str(record["id"])

            ids = [str(results[i]) for i in range(len(nodes))]
            self.logger.info(f"Created {len(ids)} nodes")
            return ids

        except Exception as e:
            self.logger.error(f"Failed to create {len(nodes)} nodes: {e}", exc_info=True)
            raise

    async def upsert_many_nodes(
        self,
        nodes: list[NodeCreate],
        conflict_properties: list[str],
    ) -> list[str]:
        self.logger.info(f"Upserting {len(nodes)} nodes")
        labels = list({node.label for node in nodes})
        self.logger.debug(
            f"labels: {truncate(str(labels), Neo4jWriter.MAX_LABEL_LENGTH)}, "
            f"first node properties: {
                truncate(str(nodes[0].properties) if nodes else '', Neo4jWriter.MAX_PROPERTIES_LENGTH)
            }, "
            f"conflict properties: {truncate(str(conflict_properties), Neo4jWriter.MAX_CONFLICT_PROPERTIES_LENGTH)}"
        )
        try:
            properties = [node.properties for node in nodes]
            self._validate_upsert_operation(labels, properties=properties, conflict_properties=conflict_properties)

            results = {}
            groups = {}
            for i, node in enumerate(nodes):
                groups.setdefault(node.label, []).append((i, node.properties))

            for label, items in groups.items():
                indices = [i for i, _ in items]
                props_list = [props for _, props in items]

                items_for_query = []
                for props in props_list:
                    match = {col: props[col] for col in conflict_properties}
                    update_props = {k: v for k, v in props.items() if k not in conflict_properties}
                    items_for_query.append({
                        "match": match,
                        "props": update_props
                    })

                query = f"""
                    UNWIND $items AS item
                    MERGE (n:{escape_identifier(label)} {{item.match}})
                    SET n += item.props
                    RETURN id(n) as id
                    """
                params = {"items": items_for_query}

                result = await self._client.execute(query, params, returning=True)
                if len(result) != len(indices):
                    raise RuntimeError(f"Expected {len(indices)} nodes for label '{label}', got {len(result)}")

                for idx, record in zip(indices, result):
                    results[idx] = str(record["id"])

            ids = [str(results[i]) for i in range(len(nodes))]
            self.logger.info(f"Upserted {len(ids)} nodes")
            return ids

        except Exception as e:
            self.logger.error(f"Failed to upsert {len(nodes)} nodes: {e}", exc_info=True)
            raise

    async def update_many_nodes(self, updates: list[NodeUpdate]) -> list[str]:
        self.logger.info(f"Updating {len(updates)} nodes")
        first_update = updates[0] if updates else None
        self.logger.debug(
            f"first update properties: {
                truncate(str(first_update.update_properties if first_update else ''), Neo4jWriter.MAX_PROPERTIES_LENGTH)
            }, "
            f"first match: {truncate(str(first_update.match if first_update else ''), Neo4jWriter.MAX_MATCH_LENGTH)}"
        )
        try:
            update_properties_list = [item.update_properties for item in updates]
            match_list = [item.match for item in updates]
            self._validate_update_operation(update_properties_list, match_list)

            match_keys = list(match_list[0].keys())
            conditions = []
            for key in match_keys:
                safe_key = escape_identifier(key)
                conditions.append(f"n.`{safe_key}` = item.`{safe_key}`")
            where_clause = " AND ".join(conditions)

            items = []
            for match, props in zip(match_list, update_properties_list):
                item = {"props": props}
                for key in match:
                    item[key] = match[key]
                items.append(item)

            query = f"""
                UNWIND $items AS item
                MATCH (n)
                WHERE {where_clause}
                SET n += item.props
                RETURN id(n) as id
                """
            params = {"items": items}

            result = await self._client.execute(query, params, returning=True)
            if len(result) != len(updates):
                raise RuntimeError(f"Expected {len(updates)} updates, got {len(result)}")
            ids = [str(record["id"]) for record in result]
            self.logger.info(f"Updated {len(ids)} nodes")
            return ids

        except Exception as e:
            self.logger.error(f"Failed to update {len(updates)} nodes: {e}", exc_info=True)
            raise

    async def update_many_nodes_by_filter(
        self,
        update_properties: dict,
        filter: FilterCondition | FilterGroup,
    ) -> list[str]:
        self.logger.info("Updating nodes by filter")
        self.logger.debug(
            f"update properties: {truncate(str(update_properties), Neo4jWriter.MAX_PROPERTIES_LENGTH)}, "
            f"filter: {truncate(str(filter), Neo4jWriter.MAX_FILTER_LENGTH)}"
        )
        try:
            self._validate_update_operation(update_properties, filter=filter)
            where_clause, params = convert_filter(filter)
            params["props"] = update_properties

            query = f"""
                MATCH (n)
                WHERE {where_clause}
                SET n += $props
                RETURN id(n) as id
                """

            result = await self._client.execute(query, params, returning=True)
            if not result:
                raise RuntimeError("No nodes found matching the filter")
            ids = [str(record["id"]) for record in result]
            self.logger.info(f"Updated {len(ids)} nodes by filter")
            return ids

        except Exception as e:
            self.logger.error(f"Failed to update nodes by filter: {e}", exc_info=True)
            raise

    async def delete_many_nodes(self, match_list: list[dict]) -> list[str]:
        self.logger.info(f"Deleting {len(match_list)} nodes")
        self.logger.debug(f"first match: {truncate(str(match_list[0]) if match_list else '', Neo4jWriter.MAX_MATCH_LENGTH)}")
        try:
            self._validate_delete_operation(match_list)
            match_keys = list(match_list[0].keys())
            conditions = []
            for key in match_keys:
                safe_key = escape_identifier(key)
                conditions.append(f"n.`{safe_key}` = match.`{safe_key}`")
            where_clause = " AND ".join(conditions)

            query = f"""
                UNWIND $match_list AS match
                MATCH (n)
                WHERE {where_clause}
                DETACH DELETE n
                RETURN id(n) as id
                """
            params = {"match_list": match_list}

            result = await self._client.execute(query, params, returning=True)
            if len(result) != len(match_list):
                raise RuntimeError(f"Expected {len(match_list)} deletions, got {len(result)}")
            ids = [str(record["id"]) for record in result]
            self.logger.info(f"Deleted {len(ids)} nodes")
            return ids

        except Exception as e:
            self.logger.error(f"Failed to delete {len(match_list)} nodes: {e}", exc_info=True)
            raise

    async def delete_many_nodes_by_filter(self, filter: FilterCondition | FilterGroup) -> list[str]:
        self.logger.info("Deleting nodes by filter")
        self.logger.debug(f"filter: {truncate(str(filter), Neo4jWriter.MAX_FILTER_LENGTH)}")
        try:
            self._validate_delete_operation(filter=filter)
            where_clause, params = convert_filter(filter)

            query = f"""
                MATCH (n)
                WHERE {where_clause}
                DETACH DELETE n
                RETURN id(n) as id
                """

            result = await self._client.execute(query, params, returning=True)
            if not result:
                raise RuntimeError("No nodes found matching the filter")
            ids = [str(record["id"]) for record in result]
            self.logger.info(f"Deleted {len(ids)} nodes by filter")
            return ids

        except Exception as e:
            self.logger.error(f"Failed to delete nodes by filter: {e}", exc_info=True)
            raise

    async def create_one_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: dict | None = None,
    ) -> str:
        self.logger.info(f"Creating one relationship of type '{rel_type}'")
        self.logger.debug(
            f"rel type: {truncate(rel_type, Neo4jWriter.MAX_REL_TYPE_LENGTH)}, "
            f"from id: {from_id}, to_id: {to_id}, "
            f"properties: {truncate(str(properties), Neo4jWriter.MAX_PROPERTIES_LENGTH)}"
        )
        try:
            self._validate_create_operation(
                rel_types=rel_type,
                from_ids=from_id,
                to_ids=to_id,
                properties=properties
            )

            query = f"""
                MATCH (a), (b)
                WHERE id(a) = $from_id AND id(b) = $to_id
                CREATE (a)-[r:`{escape_identifier(rel_type)}`]->(b)
                SET r = $props
                RETURN id(r) as id
                """
            params = {
                "from_id": int(from_id),
                "to_id": int(to_id),
                "props": properties,
            }

            result = await self._client.execute(query, params, returning=True)
            if not result:
                raise RuntimeError(f"Relationship creation failed. Node with id {from_id} or {to_id} not found.")
            rel_id = str(result[0]["id"])
            self.logger.info(f"Created relationship with id={rel_id} (type '{rel_type}')")
            return rel_id

        except Exception as e:
            self.logger.error(f"Failed to create relationship type '{rel_type}': {e}", exc_info=True)
            raise

    async def upsert_one_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: dict,
        conflict_properties: list[str],
    ) -> str:
        self.logger.info(f"Upserting one relationship of type '{rel_type}'")
        self.logger.debug(
            f"rel type: {truncate(rel_type, Neo4jWriter.MAX_REL_TYPE_LENGTH)}, "
            f"from id: {from_id}, to_id: {to_id}, "
            f"properties: {truncate(str(properties), Neo4jWriter.MAX_PROPERTIES_LENGTH)}, "
            f"conflict properties: {truncate(str(conflict_properties), Neo4jWriter.MAX_CONFLICT_PROPERTIES_LENGTH)}"
        )
        try:
            self._validate_upsert_operation(
                rel_types=rel_type,
                from_ids=from_id,
                to_ids=to_id,
                properties=properties,
                conflict_properties=conflict_properties
            )
            conditions = ", ".join(f"`{prop}`: ${prop}" for prop in conflict_properties)
            params = {prop: properties[prop] for prop in conflict_properties}
            params["from_id"] = int(from_id)
            params["to_id"] = int(to_id)
            params["props"] = {k: v for k, v in properties.items() if k not in conflict_properties}

            query = f"""
                MATCH (a), (b)
                WHERE id(a) = $from_id AND id(b) = $to_id
                MERGE (a)-[r:{escape_identifier(rel_type)} {{{conditions}}}]->(b)
                SET r += $props
                RETURN id(r) as id
                """

            result = await self._client.execute(query, params, returning=True)
            if not result:
                raise RuntimeError("Upsert relationship failed")
            rel_id = str(result[0]["id"])
            self.logger.info(f"Upserted relationship with id={rel_id} (type '{rel_type}')")
            return rel_id

        except Exception as e:
            self.logger.error(f"Failed to upsert relationship type '{rel_type}': {e}", exc_info=True)
            raise

    async def update_one_relationship(self, update_properties: dict, match: dict) -> str:
        self.logger.info("Updating one relationship by match")
        self.logger.debug(
            f"update properties: {truncate(str(update_properties), Neo4jWriter.MAX_PROPERTIES_LENGTH)}, "
            f"match: {truncate(str(match), Neo4jWriter.MAX_MATCH_LENGTH)}"
        )
        try:
            self._validate_update_operation(update_properties, match)
            conditions = []
            params = {}
            for key, value in match.items():
                conditions.append(f"r.`{escape_identifier(key)}` = ${key}")
                params[key] = value
            params["props"] = update_properties
            where_clause = " AND ".join(conditions)

            query = f"""
                MATCH ()-[r]->()
                WHERE {where_clause}
                SET r += $props
                RETURN id(r) as id
                """

            result = await self._client.execute(query, params, returning=True)
            if not result:
                raise RuntimeError("No relationship found matching the conditions")
            rel_id = str(result[0]["id"])
            self.logger.info(f"Updated relationship with id={rel_id}")
            return rel_id

        except Exception as e:
            self.logger.error(f"Failed to update relationship: {e}", exc_info=True)
            raise

    async def delete_one_relationship(self, match: dict) -> str:
        self.logger.info("Deleting one relationship by match")
        self.logger.debug(f"match: {truncate(str(match), Neo4jWriter.MAX_MATCH_LENGTH)}")
        try:
            self._validate_delete_operation(match)
            conditions = []
            params = {}
            for key, value in match.items():
                conditions.append(f"r.`{escape_identifier(key)}` = ${key}")
                params[key] = value
            where_clause = " AND ".join(conditions)

            query = f"""
                MATCH ()-[r]->()
                WHERE {where_clause}
                DELETE r
                RETURN id(r) as id
                """

            result = await self._client.execute(query, params, returning=True)
            if not result:
                raise RuntimeError("No relationship found matching the conditions")
            rel_id = str(result[0]["id"])
            self.logger.info(f"Deleted relationship with id={rel_id}")
            return rel_id

        except Exception as e:
            self.logger.error(f"Failed to delete relationship: {e}", exc_info=True)
            raise

    async def create_many_relationships(self, rels: list[RelationshipCreate]) -> list[str]:
        self.logger.info(f"Creating {len(rels)} relationships")
        rel_types = list({rel.rel_type for rel in rels})
        first_rel = rels[0] if rels else None
        self.logger.debug(
            f"rel types: {truncate(str(rel_types), Neo4jWriter.MAX_REL_TYPE_LENGTH)}, "
            f"first rel from_id: {first_rel.from_id if first_rel else None}, "
            f"first rel to_id: {first_rel.to_id if first_rel else None}"
        )
        try:
            from_ids = [item.from_id for item in rels]
            to_ids = [item.to_id for item in rels]
            properties_list = [item.properties for item in rels]
            self._validate_create_operation(
                rel_types=rel_types,
                from_ids=from_ids,
                to_ids=to_ids,
                properties=properties_list
            )

            results = {}
            groups = {}
            for i, rel in enumerate(rels):
                groups.setdefault(rel.rel_type, []).append((i, {
                    "from_id": int(rel.from_id),
                    "to_id": int(rel.to_id),
                    "props": rel.properties,
                }))

            for rel_type, items in groups.items():
                indices = [idx for idx, _ in items]
                rels_data = [data for _, data in items]

                query = f"""
                    UNWIND $rels_data AS item
                    MATCH (a), (b)
                    WHERE id(a) = item.from_id AND id(b) = item.to_id
                    CREATE (a)-[r:{escape_identifier(rel_type)}]->(b)
                    SET r = item.props
                    RETURN id(r) as id
                    """
                params = {"rels_data": rels_data}

                result = await self._client.execute(query, params, returning=True)
                if len(result) != len(indices):
                    raise RuntimeError(
                        f"Expected {len(indices)} relationships, "
                        f"got {len(result)} for type '{rel_type}'"
                    )

                for idx, record in zip(indices, result):
                    results[idx] = str(record["id"])

            ids = [str(results[i]) for i in range(len(rels))]
            self.logger.info(f"Created {len(ids)} relationships")
            return ids

        except Exception as e:
            self.logger.error(f"Failed to create {len(rels)} relationships: {e}", exc_info=True)
            raise

    async def upsert_many_relationships(
        self,
        rels: list[RelationshipCreate],
        conflict_properties: list[str]
    ) -> list[str]:
        self.logger.info(f"Upserting {len(rels)} relationships")
        rel_types = list({rel.rel_type for rel in rels})
        first_rel = rels[0] if rels else None
        self.logger.debug(
            f"rel types: {truncate(str(rel_types), Neo4jWriter.MAX_REL_TYPE_LENGTH)}, "
            f"first rel from id: {first_rel.from_id if first_rel else None}, "
            f"first rel to id: {first_rel.to_id if first_rel else None}, "
            f"conflict properties: {truncate(str(conflict_properties), Neo4jWriter.MAX_CONFLICT_PROPERTIES_LENGTH)}"
        )
        try:
            from_ids = [item.from_id for item in rels]
            to_ids = [item.to_id for item in rels]
            properties_list = [item.properties for item in rels]
            self._validate_upsert_operation(
                rel_types=rel_types,
                from_ids=from_ids,
                to_ids=to_ids,
                properties=properties_list,
                conflict_properties=conflict_properties
            )

            results = {}
            groups = {}
            for i, rel in enumerate(rels):
                groups.setdefault(rel.rel_type, []).append((i, {
                    "from_id": int(rel.from_id),
                    "to_id": int(rel.to_id),
                    "props": rel.properties,
                }))

            for rel_type, items in groups.items():
                indices = [idx for idx, _ in items]

                items_data = []
                for _, data in items:
                    match = {prop: data["props"][prop] for prop in conflict_properties}
                    update_props = {k: v for k, v in data["props"].items() if k not in conflict_properties}
                    items_data.append({
                        "from_id": data["from_id"],
                        "to_id": data["to_id"],
                        "match": match,
                        "props": update_props
                    })

                query = f"""
                    UNWIND $items_data AS item
                    MATCH (a), (b)
                    WHERE id(a) = item.from_id AND id(b) = item.to_id
                    MERGE (a)-[r:{escape_identifier(rel_type)} {{item.match}}]->(b)
                    SET r += item.props
                    RETURN id(r) as id
                    """

                params = {"items_data": items_data}
                result = await self._client.execute(query, params, returning=True)
                if len(result) != len(indices):
                    raise RuntimeError(f"Expected {len(indices)} upserts, got {len(result)} for type '{rel_type}'")

                for idx, record in zip(indices, result):
                    results[idx] = str(record["id"])

            ids = [str(results[i]) for i in range(len(rels))]
            self.logger.info(f"Upserted {len(ids)} relationships")
            return ids

        except Exception as e:
            self.logger.error(f"Failed to upsert {len(rels)} relationships: {e}", exc_info=True)
            raise

    async def update_many_relationships(self, updates: list[RelationshipUpdate]) -> list[str]:
        self.logger.info(f"Updating {len(updates)} relationships")
        first_update = updates[0] if updates else None
        self.logger.debug(
            f"first update properties: {
                truncate(str(first_update.update_properties if first_update else ''), Neo4jWriter.MAX_PROPERTIES_LENGTH)
            }, "
            f"first match: {truncate(str(first_update.match if first_update else ''), Neo4jWriter.MAX_MATCH_LENGTH)}"
        )
        try:
            match_list = [item.match for item in updates]
            update_properties_list = [item.update_properties for item in updates]
            self._validate_update_operation(update_properties_list, match_list)

            match_keys = list(updates[0].match.keys())
            conditions = []
            for key in match_keys:
                safe_key = escape_identifier(key)
                conditions.append(f"r.`{safe_key}` = item.`{safe_key}`")
            where_clause = " AND ".join(conditions)

            items = []
            for update in updates:
                item = {"props": update.update_properties}
                for key, value in update.match.items():
                    item[key] = value
                items.append(item)

            query = f"""
                UNWIND $items AS item
                MATCH ()-[r]->()
                WHERE {where_clause}
                SET r += item.props
                RETURN id(r) as id
                """
            params = {"items": items}

            result = await self._client.execute(query, params, returning=True)
            if len(result) != len(updates):
                raise RuntimeError(f"Expected {len(updates)} updates, got {len(result)}")
            ids = [str(record["id"]) for record in result]
            self.logger.info(f"Updated {len(ids)} relationships")
            return ids

        except Exception as e:
            self.logger.error(f"Failed to update {len(updates)} relationships: {e}", exc_info=True)
            raise

    async def update_many_relationships_by_filter(
        self,
        update_properties: dict,
        filter: FilterCondition | FilterGroup,
    ) -> list[str]:
        self.logger.info("Updating relationships by filter")
        self.logger.debug(
            f"update properties: {truncate(str(update_properties), Neo4jWriter.MAX_PROPERTIES_LENGTH)}, "
            f"filter: {truncate(str(filter), Neo4jWriter.MAX_FILTER_LENGTH)}"
        )
        try:
            self._validate_update_operation(update_properties, filter=filter)
            where_clause, params = convert_filter(filter)
            params["props"] = update_properties

            query = f"""
                MATCH ()-[r]->()
                WHERE {where_clause}
                SET r += $props
                RETURN id(r) as id
                """

            result = await self._client.execute(query, params, returning=True)
            if not result:
                raise RuntimeError("No relationships found matching the filter")
            ids = [str(record["id"]) for record in result]
            self.logger.info(f"Updated {len(ids)} relationships by filter")
            return ids

        except Exception as e:
            self.logger.error(f"Failed to update relationships by filter: {e}", exc_info=True)
            raise

    async def delete_many_relationships(self, match_list: list[dict]) -> list[str]:
        self.logger.info(f"Deleting {len(match_list)} relationships")
        self.logger.debug(f"first match: {
            truncate(str(match_list[0] if match_list else ''), Neo4jWriter.MAX_MATCH_LENGTH)
        }")
        try:
            self._validate_delete_operation(match_list)
            match_keys = list(match_list[0].keys())
            conditions = []
            for key in match_keys:
                safe_key = escape_identifier(key)
                conditions.append(f"r.`{safe_key}` = match.`{safe_key}`")
            where_clause = " AND ".join(conditions)

            query = f"""
                UNWIND $match_list AS match
                MATCH ()-[r]->()
                WHERE {where_clause}
                DELETE r
                RETURN id(r) as id
                """
            params = {"match_list": match_list}

            result = await self._client.execute(query, params, returning=True)
            if len(result) != len(match_list):
                raise RuntimeError(f"Expected {len(match_list)} deletions, got {len(result)}")
            ids = [str(record["id"]) for record in result]
            self.logger.info(f"Deleted {len(ids)} relationships")
            return ids

        except Exception as e:
            self.logger.error(f"Failed to delete {len(match_list)} relationships: {e}", exc_info=True)
            raise

    async def delete_many_relationships_by_filter(self, filter: FilterCondition | FilterGroup) -> list[str]:
        self.logger.info("Deleting relationships by filter")
        self.logger.debug(f"filter: {truncate(str(filter), Neo4jWriter.MAX_FILTER_LENGTH)}")
        try:
            self._validate_delete_operation(filter=filter)
            where_clause, params = convert_filter(filter)

            query = f"""
                MATCH ()-[r]->()
                WHERE {where_clause}
                DELETE r
                RETURN id(r) as id
                """

            result = await self._client.execute(query, params, returning=True)
            if not result:
                raise RuntimeError("No relationships found matching the filter")
            ids = [str(record["id"]) for record in result]
            self.logger.info(f"Deleted {len(ids)} relationships by filter")
            return ids

        except Exception as e:
            self.logger.error(f"Failed to delete relationships by filter: {e}", exc_info=True)
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
