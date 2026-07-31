from typing import Any
from functools import partial
from logging import Logger
from antlr4 import InputStream, CommonTokenStream
from antlr4_cypher import CypherLexer, CypherParser
from src.data.db.nosql.graph.neo4j.client import Neo4jAsyncClient
from src.data.db.nosql.graph.base import (
    BaseGraphWriter,
    NodeCreate,
    NodeUpdate,
    RelationshipCreate,
    RelationshipUpdate,
)
from src.utils.truncate import truncate


class Neo4jWriter(BaseGraphWriter):
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
    MAX_PROPERTIES_LENGTH = 500
    MAX_CONFLICT_PROPERTIES_LENGTH = 500
    MAX_MATCH_LENGTH = 500
    MAX_FILTER_LENGTH = 500
    MAX_QUERY_LENGTH = 500
    MAX_REL_TYPE_LENGTH = 500

    def __init__(self, client: Neo4jAsyncClient, logger: Logger, **kwargs):
        super().__init__(**kwargs)
        self._client = client
        self.logger = logger or client.logger

    @staticmethod
    def _validate_strings_exist(strings: str | list[str], context: str = "") -> str | None:
        prefix = f"[{context}] " if context else ""
        if not strings:
            return f"{prefix}Argument cannot be empty"

        if isinstance(strings, list):
            error_lines = []
            for i, value in enumerate(strings):
                if not value:
                    error_lines.append(f"Item {i}: string is empty.")
                    if len(error_lines) >= Neo4jWriter.MAX_VALIDATION_ERRORS:
                        error_lines.append("... (and more errors, truncated)")
                        break
            if error_lines:
                return f"{prefix}Validation errors for strings:\n" + "\n".join(error_lines)

    @staticmethod
    def _validate_dict_exist(data: dict[str, Any] | list[dict[str, Any]], context: str = "") -> str | None:
        prefix = f"[{context}] " if context else ""
        if not data:
            return f"{prefix}Data cannot be empty."
        if isinstance(data, list):
            empty_indices = []
            for i, item in enumerate(data):
                if not item:
                    empty_indices.append(i)
                    if len(empty_indices) >= Neo4jWriter.MAX_VALIDATION_ERRORS:
                        empty_indices.append("...")
                        break

            if empty_indices:
                if len(empty_indices) == 1:
                    return f"{prefix}Item at index {empty_indices[0]} is empty."
                else:
                    indices_str = ", ".join(str(i) for i in empty_indices if i != "...")
                    msg = f"{prefix}Items at indices {indices_str} are empty."
                    if "..." in empty_indices:
                        msg += " (and more errors, truncated)"
                    return msg

    @staticmethod
    def _validate_dict_contains_consistent_keys(data_list: list[dict[str, Any]], context: str = "") -> str | None:
        prefix = f"[{context}] " if context else ""
        first_keys = set(data_list[0].keys())
        error_lines = []
        for i, data in enumerate(data_list[1:], start=1):
            current_keys = set(data.keys())
            if first_keys != current_keys:
                missing = first_keys - current_keys
                extra = current_keys - first_keys
                parts = []
                if missing:
                    parts.append(f"missing keys: {sorted(missing)}")
                if extra:
                    parts.append(f"extra keys: {sorted(extra)}")
                error_lines.append(f"[Item {i}] Inconsistent keys: " + ", ".join(parts))
                if len(error_lines) >= Neo4jWriter.MAX_VALIDATION_ERRORS:
                    error_lines.append("... (and more errors, truncated)")
                    break

        if error_lines:
            return (
                    f"{prefix}Inconsistent keys across dictionaries.\n"
                    f"Expected keys (from first item): {sorted(first_keys)}\n" +
                    "\n".join(error_lines)
            )

    @staticmethod
    def _validate_all_conflict_properties_in_properties(
        properties: dict[str, Any] | list[dict[str, Any]],
        conflict_properties: list[str]
    ) -> str | None:
        error_lines = []
        if isinstance(properties, dict):
            for prop in conflict_properties:
                if prop not in properties:
                    error_lines.append(f"Conflict property '{prop}' is missing in properties")
                elif not properties[prop]:
                    error_lines.append(f"Conflict property '{prop}' is empty")
                if len(error_lines) >= Neo4jWriter.MAX_VALIDATION_ERRORS:
                    error_lines.append("... (and more errors, truncated)")
                    break

        else:
            for i, item in enumerate(properties):
                for prop in conflict_properties:
                    if prop not in item:
                        error_lines.append(f"[Item {i}] Conflict property '{prop}' is missing")
                    elif not item[prop]:
                        error_lines.append(f"[Item {i}] Conflict property '{prop}' is empty")
                    if len(error_lines) >= Neo4jWriter.MAX_VALIDATION_ERRORS:
                        error_lines.append("... (and more errors, truncated)")
                        break

        if error_lines:
            return (
                f"[Properties] Validation errors for conflict properties.\n"
                f"Expected conflict properties: {sorted(conflict_properties)}\n" +
                "\n".join(error_lines)
            )

    @staticmethod
    def _validate_match_not_contains_duplicates(match: list[dict[str, Any]]) -> str | None:
        seen = {}
        duplicates = []
        for i, item in enumerate(match):
            key = frozenset(item.items())
            if key in seen:
                duplicates.append(f"index {i} duplicates index {seen[key]}")
            else:
                seen[key] = i
        if duplicates:
            return f"[Match] Duplicate match conditions found: {', '.join(duplicates)}"

    @staticmethod
    def _validate_operators_in_filter(filter: dict[str, Any]) -> str | None:
        for key in filter.keys():
            if "__" in key:
                operator = key.split("__")[1]
                if operator not in Neo4jWriter.ALLOWED_FILTER_OPS:
                    return f"[Filter] Unsupported operator '{operator}' in key '{key}'."

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
    def _run_validation(checks: list[partial]):
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
        checks = []
        if isinstance(labels, list):
            checks.append(partial(Neo4jWriter._validate_strings_exist, labels, "Labels"))
        return checks

    @staticmethod
    def _validate_rel_types_partials(rel_types: str | list[str]) -> list[partial]:
        checks = []
        if isinstance(rel_types, list):
            checks.append(partial(Neo4jWriter._validate_strings_exist, rel_types, "Relationship types"))
        return checks

    @staticmethod
    def _validate_from_ids(from_ids: str | list[str]) -> list[partial]:
        return [partial(Neo4jWriter._validate_strings_exist, from_ids, "From ids")]

    @staticmethod
    def _validate_to_ids(to_ids: str | list[str]) -> list[partial]:
        return [partial(Neo4jWriter._validate_strings_exist, to_ids, "To ids")]

    @staticmethod
    def _validate_properties_partials(properties: dict[str, Any] | list[dict[str, Any]]) -> list[partial]:
        return [partial(Neo4jWriter._validate_dict_exist, properties, "Properties")]

    @staticmethod
    def _validate_update_properties_partials(update_properties: dict[str, Any] | list[dict[str, Any]]) -> list[partial]:
        return [partial(Neo4jWriter._validate_dict_exist, update_properties, "Update properties")]

    @staticmethod
    def _validate_conflict_properties_partials(conflict_properties: list[str]) -> list[partial]:
        return [partial(Neo4jWriter._validate_strings_exist, conflict_properties, "Conflict properties")]

    @staticmethod
    def _validate_match_partials(match: dict[str, Any] | list[dict[str, Any]]) -> list[partial]:
        checks = [partial(Neo4jWriter._validate_dict_exist, match, "Match")]
        if isinstance(match, list):
            checks.extend([
                partial(Neo4jWriter._validate_match_not_contains_duplicates, match),
                partial(Neo4jWriter._validate_dict_contains_consistent_keys, match, "Match"),
            ])
        return checks

    @staticmethod
    def _validate_filter_partials(filter: dict[str, Any]):
        return [
            partial(Neo4jWriter._validate_dict_exist, filter, "Filter"),
            partial(Neo4jWriter._validate_operators_in_filter, filter),
        ]

    @staticmethod
    def _validate_create_operation(
        labels: str | list[str] | None = None,
        rel_types: str | list[str] | None = None,
        from_ids: Any | list[Any] | None = None,
        to_ids: Any | list[Any] | None = None,
        properties: dict[str, Any] | list[dict[str, Any]] | None = None
    ) -> None:
        checks = []
        if labels:
            checks.extend(Neo4jWriter._validate_labels_partials(labels))
        if rel_types:
            checks.extend(Neo4jWriter._validate_rel_types_partials(rel_types))
        if from_ids:
            checks.extend(Neo4jWriter._validate_from_ids(from_ids))
        if to_ids:
            checks.extend(Neo4jWriter._validate_to_ids(to_ids))
        if properties:
            checks.extend(Neo4jWriter._validate_properties_partials(properties))
        if checks:
            Neo4jWriter._run_validation(checks)

    @staticmethod
    def _validate_upsert_operation(
        labels: str | list[str] | None = None,
        rel_types: str | list[str] | None = None,
        from_ids: Any | list[Any] | None = None,
        to_ids: Any | list[Any] | None = None,
        properties: dict[str, Any] | list[dict[str, Any]] | None = None,
        conflict_properties: list[str] | None = None,
    ) -> None:
        checks = []
        if labels:
            checks.extend(Neo4jWriter._validate_labels_partials(labels))
        if rel_types:
            checks.extend(Neo4jWriter._validate_rel_types_partials(rel_types))
        if from_ids:
            checks.extend(Neo4jWriter._validate_from_ids(from_ids))
        if to_ids:
            checks.extend(Neo4jWriter._validate_to_ids(to_ids))
        if properties:
            checks.extend(Neo4jWriter._validate_properties_partials(properties))
        if conflict_properties:
            checks.extend(Neo4jWriter._validate_conflict_properties_partials(conflict_properties))
            checks.append(partial(
                Neo4jWriter._validate_all_conflict_properties_in_properties,
                properties,
                conflict_properties)
            )
        if checks:
            Neo4jWriter._run_validation(checks)

    @staticmethod
    def _validate_update_operation(
        update_properties: dict[str, Any] | list[dict[str, Any]] | None = None,
        match: dict[str, Any] | list[dict[str, Any]] | None = None,
        filter: dict[str, Any] | None = None,
    ) -> None:
        checks = []
        if update_properties:
            checks.extend(Neo4jWriter._validate_update_properties_partials(update_properties))
        if match:
            checks.extend(Neo4jWriter._validate_match_partials(match))
        if filter:
            checks.extend(Neo4jWriter._validate_filter_partials(filter))
        if checks:
            Neo4jWriter._run_validation(checks)

    @staticmethod
    def _validate_delete_operation(
        match: dict[str, Any] | list[dict[str, Any]] | None = None,
        filter: dict[str, Any] | None = None,
    ) -> None:
        checks = []
        if match:
            checks.extend(Neo4jWriter._validate_match_partials(match))
        if filter:
            checks.extend(Neo4jWriter._validate_filter_partials(filter))
        if checks:
            Neo4jWriter._run_validation(checks)

    @staticmethod
    def _escape_identifier(name: str) -> str:
        return f"`{name.replace('`', '``')}`"

    def _build_filter_conditions(self, filter: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        conditions = []
        params = {}
        for key, value in filter.items():
            if "__" in key:
                field, operator = key.split("__", 1)
            else:
                field, operator = key, "eq"

            safe_field = self._escape_identifier(field)
            param_name = f"filter_{len(params)}"

            if operator == "eq":
                conditions.append(f"n.`{safe_field}` = ${param_name}")
            elif operator == "gt":
                conditions.append(f"n.`{safe_field}` > ${param_name}")
            elif operator == "lt":
                conditions.append(f"n.`{safe_field}` < ${param_name}")
            elif operator == "gte":
                conditions.append(f"n.`{safe_field}` >= ${param_name}")
            elif operator == "lte":
                conditions.append(f"n.`{safe_field}` <= ${param_name}")
            elif operator == "ne":
                conditions.append(f"n.`{safe_field}` <> ${param_name}")
            elif operator == "in":
                if not isinstance(value, list) or not value:
                    raise ValueError(f"IN operator requires non-empty list for field '{field}'")
                conditions.append(f"n.`{safe_field}` IN ${param_name}")
            elif operator == "isnull":
                if value is True:
                    conditions.append(f"n.`{safe_field}` IS NULL")
                else:
                    conditions.append(f"n.`{safe_field}` IS NOT NULL")
                continue
            elif operator == "like":
                conditions.append(f"n.`{safe_field}` CONTAINS ${param_name}")
            elif operator == "ilike":
                conditions.append(f"toLower(n.`{safe_field}`) CONTAINS toLower(${param_name})")
            else:
                raise ValueError(f"Unsupported operator '{operator}'")

            params[param_name] = value

        where_clause = " AND ".join(conditions) if conditions else ""
        return where_clause, params

    async def write_query(
        self,
        query: str,
        params: dict[str, Any] | list[dict[str, Any]] | None = None
    ) -> list[dict[str, Any]]:
        self.logger.debug(f"Executing raw write query")
        try:
            self._validate_write_query(query)
            result = await self._client.execute(query, params, returning=True)
            self.logger.debug(f"Write query executed successfully, returned {len(result)} records")
            return result

        except Exception as e:
            self.logger.error(f"Write query failed: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        self.logger.debug("Closing Neo4jWriter client")
        await self._client.close()
        self.logger.debug("Neo4jWriter client closed")

    async def create_one_node(self, label: str, properties: dict[str, Any]) -> str:
        self.logger.info(f"Creating one node with label '{label}'")
        self.logger.debug(
            f"label: {truncate(label, Neo4jWriter.MAX_LABEL_LENGTH)}, "
            f"properties: {truncate(str(properties), Neo4jWriter.MAX_PROPERTIES_LENGTH)}"
        )
        try:
            self._validate_create_operation(label, properties=properties)
            query = f"CREATE (n:`{self._escape_identifier(label)}` $props) RETURN id(n) as id"

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
        properties: dict[str, Any],
        conflict_properties: list[str] | None = None,
    ) -> str:
        self.logger.info(f"Upserting one node with label '{label}'")
        self.logger.debug(
            f"label: {truncate(label, Neo4jWriter.MAX_LABEL_LENGTH)}, "
            f"properties: {truncate(str(properties), Neo4jWriter.MAX_PROPERTIES_LENGTH)}, "
            f"conflict_properties: {truncate(str(conflict_properties), Neo4jWriter.MAX_CONFLICT_PROPERTIES_LENGTH)}"
        )
        try:
            self._validate_upsert_operation(label, properties=properties, conflict_properties=conflict_properties)
            conditions = ", ".join(f"`{col}`: ${col}" for col in conflict_properties)
            params = {col: properties[col] for col in conflict_properties}
            params["props"] = {k: v for k, v in properties.items() if k not in conflict_properties}
            query = f"""
                MERGE (n:`{self._escape_identifier(label)}` {{{conditions}}})
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

    async def update_one_node(self, update_properties: dict[str, Any], match: dict[str, Any]) -> str:
        self.logger.info("Updating one node by match")
        self.logger.debug(
            f"update_properties: {truncate(str(update_properties), Neo4jWriter.MAX_PROPERTIES_LENGTH)}, "
            f"match: {truncate(str(match), Neo4jWriter.MAX_MATCH_LENGTH)}"
        )
        try:
            self._validate_update_operation(update_properties, match)
            conditions = []
            params = {}
            for key, value in match.items():
                conditions.append(f"n.`{self._escape_identifier(key)}` = ${key}")
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

    async def delete_one_node(self, match: dict[str, Any]) -> str:
        self.logger.info("Deleting one node by match")
        self.logger.debug(f"match: {truncate(str(match), Neo4jWriter.MAX_MATCH_LENGTH)}")
        try:
            self._validate_delete_operation(match)
            conditions = []
            params = {}
            for key, value in match.items():
                conditions.append(f"n.`{self._escape_identifier(key)}` = ${key}")
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
                    CREATE (n:`{self._escape_identifier(label)}` props)
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
            f"conflict_properties: {truncate(str(conflict_properties), Neo4jWriter.MAX_CONFLICT_PROPERTIES_LENGTH)}"
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
                    MERGE (n:{self._escape_identifier(label)} {{item.match}})
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
                safe_key = self._escape_identifier(key)
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

    async def update_many_nodes_by_filter(self, update_properties: dict[str, Any], filter: dict[str, Any]) -> list[str]:
        self.logger.info("Updating nodes by filter")
        self.logger.debug(
            f"update_properties: {truncate(str(update_properties), Neo4jWriter.MAX_PROPERTIES_LENGTH)}, "
            f"filter: {truncate(str(filter), Neo4jWriter.MAX_FILTER_LENGTH)}"
        )
        try:
            self._validate_update_operation(update_properties, filter=filter)
            where_clause, params = self._build_filter_conditions(filter)
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

    async def delete_many_nodes(self, match_list: list[dict[str, Any]]) -> list[str]:
        self.logger.info(f"Deleting {len(match_list)} nodes")
        self.logger.debug(f"first match: {
            truncate(str(match_list[0]) if match_list else '', Neo4jWriter.MAX_MATCH_LENGTH)
        }")
        try:
            self._validate_delete_operation(match_list)
            match_keys = list(match_list[0].keys())
            conditions = []
            for key in match_keys:
                safe_key = self._escape_identifier(key)
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

    async def delete_many_nodes_by_filter(self, filter: dict[str, Any]) -> list[str]:
        self.logger.info("Deleting nodes by filter")
        self.logger.debug(f"filter: {truncate(str(filter), Neo4jWriter.MAX_FILTER_LENGTH)}")
        try:
            self._validate_delete_operation(filter=filter)
            where_clause, params = self._build_filter_conditions(filter)

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
        properties: dict[str, Any] | None = None,
    ) -> str:
        self.logger.info(f"Creating one relationship of type '{rel_type}'")
        self.logger.debug(
            f"rel_type: {truncate(rel_type, Neo4jWriter.MAX_REL_TYPE_LENGTH)}, "
            f"from_id: {from_id}, to_id: {to_id}, "
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
                CREATE (a)-[r:`{self._escape_identifier(rel_type)}`]->(b)
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
        properties: dict[str, Any],
        conflict_properties: list[str],
    ) -> str:
        self.logger.info(f"Upserting one relationship of type '{rel_type}'")
        self.logger.debug(
            f"rel_type: {truncate(rel_type, Neo4jWriter.MAX_REL_TYPE_LENGTH)}, "
            f"from_id: {from_id}, to_id: {to_id}, "
            f"properties: {truncate(str(properties), Neo4jWriter.MAX_PROPERTIES_LENGTH)}, "
            f"conflict_properties: {truncate(str(conflict_properties), Neo4jWriter.MAX_CONFLICT_PROPERTIES_LENGTH)}"
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
                MERGE (a)-[r:{self._escape_identifier(rel_type)} {{{conditions}}}]->(b)
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

    async def update_one_relationship(self, update_properties: dict[str, Any], match: dict[str, Any]) -> str:
        self.logger.info("Updating one relationship by match")
        self.logger.debug(
            f"update_properties: {truncate(str(update_properties), Neo4jWriter.MAX_PROPERTIES_LENGTH)}, "
            f"match: {truncate(str(match), Neo4jWriter.MAX_MATCH_LENGTH)}"
        )
        try:
            self._validate_update_operation(update_properties, match)
            conditions = []
            params = {}
            for key, value in match.items():
                conditions.append(f"r.`{self._escape_identifier(key)}` = ${key}")
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

    async def delete_one_relationship(self, match: dict[str, Any]) -> str:
        self.logger.info("Deleting one relationship by match")
        self.logger.debug(f"match: {truncate(str(match), Neo4jWriter.MAX_MATCH_LENGTH)}")
        try:
            self._validate_delete_operation(match)
            conditions = []
            params = {}
            for key, value in match.items():
                conditions.append(f"r.`{self._escape_identifier(key)}` = ${key}")
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
            f"rel_types: {truncate(str(rel_types), Neo4jWriter.MAX_REL_TYPE_LENGTH)}, "
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
                    CREATE (a)-[r:{self._escape_identifier(rel_type)}]->(b)
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
        conflict_properties: list[str],
    ) -> list[str]:
        self.logger.info(f"Upserting {len(rels)} relationships")
        rel_types = list({rel.rel_type for rel in rels})
        first_rel = rels[0] if rels else None
        self.logger.debug(
            f"rel_types: {truncate(str(rel_types), Neo4jWriter.MAX_REL_TYPE_LENGTH)}, "
            f"first rel from_id: {first_rel.from_id if first_rel else None}, "
            f"first rel to_id: {first_rel.to_id if first_rel else None}, "
            f"conflict_properties: {truncate(str(conflict_properties), Neo4jWriter.MAX_CONFLICT_PROPERTIES_LENGTH)}"
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
                    MERGE (a)-[r:{self._escape_identifier(rel_type)} {{item.match}}]->(b)
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
                safe_key = self._escape_identifier(key)
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
        update_properties: dict[str, Any],
        filter: dict[str, Any],
    ) -> list[str]:
        self.logger.info("Updating relationships by filter")
        self.logger.debug(
            f"update_properties: {truncate(str(update_properties), Neo4jWriter.MAX_PROPERTIES_LENGTH)}, "
            f"filter: {truncate(str(filter), Neo4jWriter.MAX_FILTER_LENGTH)}"
        )
        try:
            self._validate_update_operation(update_properties, filter=filter)
            where_clause, params = self._build_filter_conditions(filter)
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

    async def delete_many_relationships(self, match_list: list[dict[str, Any]]) -> list[str]:
        self.logger.info(f"Deleting {len(match_list)} relationships")
        self.logger.debug(f"first match: {
            truncate(str(match_list[0] if match_list else ''), Neo4jWriter.MAX_MATCH_LENGTH)
        }")
        try:
            self._validate_delete_operation(match_list)
            match_keys = list(match_list[0].keys())
            conditions = []
            for key in match_keys:
                safe_key = self._escape_identifier(key)
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

    async def delete_many_relationships_by_filter(self, filter: dict[str, Any]) -> list[str]:
        self.logger.info("Deleting relationships by filter")
        self.logger.debug(f"filter: {truncate(str(filter), Neo4jWriter.MAX_FILTER_LENGTH)}")
        try:
            self._validate_delete_operation(filter=filter)
            where_clause, params = self._build_filter_conditions(filter)

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
