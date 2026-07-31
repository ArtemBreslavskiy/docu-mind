import sqlparse
from logging import Logger
from typing import Any
from functools import partial
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import tuple_, MetaData, Table, update, delete, case, text, PrimaryKeyConstraint, UniqueConstraint
from src.data.db.sql.base import BaseSQLWriter, SQLUpdate
from src.data.db.sql.postgres.client import PostgresAsyncClient
from src.utils.truncate import truncate


class PostgresWriter(BaseSQLWriter):
    WRITE_TYPES = {"INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "MERGE"}
    ALLOWED_FILTER_OPS = {"gt", "lt", "gte", "lte", "ne", "in", "isnull", "like", "ilike"}
    MAX_VALIDATION_ERRORS = 20
    MAX_TABLE_NAME_LENGTH = 500
    MAX_DATA_LENGTH = 500
    MAX_CONFLICT_COLUMNS_LENGTH = 500
    MAX_MATCH_LENGTH = 500
    MAX_FILTER_LENGTH = 500

    def __init__(
        self,
        client: PostgresAsyncClient,
        logger: Logger | None = None,
        default_schema: str = "public", **kwargs
    ):
        super().__init__(**kwargs)
        self.client = client
        self.logger = logger or client.logger
        self.metadata = MetaData()
        self.default_schema = default_schema
        self._tables_cache: dict[tuple[str, str], Table] = {}     # tuple[schema, table_name]

    @staticmethod
    def _validate_table_has_primary_key(table: Table) -> str | None:
        if not table.primary_key.columns:
            return f"[Table '{table.name}'] Table has no primary key."

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
                    if len(empty_indices) >= PostgresWriter.MAX_VALIDATION_ERRORS:
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
    def _validate_dict_not_contains_pk(
        table: Table,
        update_data: dict[str, Any] | list[dict[str, Any]],
        context: str = "",
    ) -> str | None:
        prefix = f"[{context}, Table '{table.name}'] " if context else f"[Table '{table.name}'] "
        pk_name = table.primary_key.columns[0].name
        if isinstance(update_data, dict):
            if pk_name in update_data:
                return f"{prefix}Cannot update primary key column '{pk_name}'."
        else:
            error_indices = []
            for i, item in enumerate(update_data):
                if pk_name in item:
                    error_indices.append(i)
                    if len(error_indices) >= PostgresWriter.MAX_VALIDATION_ERRORS:
                        error_indices.append("...")
                        break

            if error_indices:
                if len(error_indices) == 1:
                    return (
                        f"{prefix}Primary key column '{pk_name}' "
                        f"cannot be updated in item at index {error_indices[0]}."
                    )
                else:
                    indices_str = ", ".join(str(i) for i in error_indices if i != "...")
                    msg = (
                        f"{prefix}Primary key column '{pk_name}' "
                        f"cannot be updated in items at indices: {indices_str}."
                    )
                    if "..." in error_indices:
                        msg += " (and more errors, truncated)"
                    return msg

    @staticmethod
    def _validate_dict_not_contains_extra_names(
        table: Table,
        data: dict[str, Any] | list[dict[str, Any]],
        context: str = "",
    ) -> str | None:
        prefix = f"[{context}, Table '{table.name}'] " if context else f"[Table '{table.name}'] "
        if isinstance(data, dict):
            msg = PostgresWriter._validate_columns_in_table(table, list(data.keys()))
            if msg:
                return f"{prefix}{msg}"
        else:
            error_lines = []
            for i, item in enumerate(data):
                msg = PostgresWriter._validate_columns_in_table(table, list(item.keys()))
                if msg:
                    error_lines.append(f"[Item {i}] {msg}")
                    if len(error_lines) >= PostgresWriter.MAX_VALIDATION_ERRORS:
                        error_lines.append("... (and more errors, truncated)")
                        break
            if error_lines:
                return f"{prefix}Invalid column names:\n" + "\n".join(error_lines)

    @staticmethod
    def _validate_dict_contains_values_for_not_null_columns(
        table: Table,
        data: dict[str, Any] | list[dict[str, Any]],
        context: str = "",
    ) -> str | None:
        prefix = f"[{context}, Table '{table.name}'] " if context else f"[Table '{table.name}'] "
        required = {
            col.name for col in table.c
            if not col.nullable and col.default is None and col.server_default is None
        }
        if not required:
            return

        error_lines = []
        if isinstance(data, dict):
            missing = required - set(data.keys())
            if missing:
                error_lines.append(f"Missing required NOT NULL columns: {sorted(missing)}.")
            for col in required:
                if col in data and data[col] is None:
                    error_lines.append(f"Column '{col}' has NULL value, but is NOT NULL.")
                    if len(error_lines) >= PostgresWriter.MAX_VALIDATION_ERRORS:
                        error_lines.append("... (and more errors, truncated)")
                        break
        else:
            for i, item in enumerate(data):
                missing = required - set(item.keys())
                if missing:
                    error_lines.append(f"[Item {i}] Missing required NOT NULL columns: {sorted(missing)}.")
                    if len(error_lines) >= PostgresWriter.MAX_VALIDATION_ERRORS:
                        error_lines.append("... (and more errors, truncated)")
                        break
                for col in required:
                    if col in item and item[col] is None:
                        error_lines.append(f"[Item {i}] Column '{col}' has NULL value, but is NOT NULL.")
                        if len(error_lines) >= PostgresWriter.MAX_VALIDATION_ERRORS:
                            error_lines.append("... (and more errors, truncated)")
                            break
        if error_lines:
            return f"{prefix} NOT NULL validation failed:\n" + "\n".join(error_lines)

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
                if len(error_lines) >= PostgresWriter.MAX_VALIDATION_ERRORS:
                    error_lines.append("... (and more errors, truncated)")
                    break

        if error_lines:
            return (
                f"{prefix}Inconsistent keys across dictionaries.\n"
                f"Expected keys (from first item): {sorted(first_keys)}\n" +
                "\n".join(error_lines)
            )

    @staticmethod
    def _validate_columns_exist(columns: list[str], context: str = "") -> str | None:
        prefix = f"[{context}] " if context else ""
        if not columns:
            return f"{prefix}Columns list cannot be empty."

    @staticmethod
    def _validate_columns_in_table(table: Table, columns: str | list[str], context: str = "") -> str | None:
        prefix = f"[{context}] " if context else ""
        if isinstance(columns, str):
            if columns not in table.c:
                return f"{prefix}Column '{columns}' not found in table '{table.name}'."
        else:
            missing = [col for col in columns if col not in table.c]
            if missing:
                return f"{prefix}Columns not found in table '{table.name}': {', '.join(missing)}."

    @staticmethod
    def _validate_columns_unique(table: Table, columns: str | list[str], context: str = "") -> str | None:
        prefix = f"[{context}] " if context else ""
        required = set(columns)
        found = False
        for constraint in table.constraints:
            if isinstance(constraint, (PrimaryKeyConstraint, UniqueConstraint)):
                if required == ({c.name for c in constraint.columns}):
                    found = True
                    break
        if not found:
            if isinstance(columns, list):
                return f"{prefix}No UNIQUE or PRIMARY KEY constraint found for columns: {', '.join(columns)}"
            else:
                return f"{prefix}No UNIQUE or PRIMARY KEY constraint found for column: {columns}"

    @staticmethod
    def _validate_operators_in_filter(filter: dict[str, Any]) -> str | None:
        for key in filter.keys():
            if "__" in key:
                operator = key.split("__")[1]
                if operator not in PostgresWriter.ALLOWED_FILTER_OPS:
                    return f"[Filter] Unsupported operator '{operator}' in key '{key}'."

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
    def _validate_write_query(query: str) -> None:
        parsed = sqlparse.parse(query)
        if not parsed:
            raise ValueError("Empty query")
        for stmt in parsed:
            query_type = stmt.get_type()
            if query_type not in PostgresWriter.WRITE_TYPES:
                raise ValueError(f"Write query expected, got: {query_type}")

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
    def _validate_data_partials(table: Table, data: dict[str, Any] | list[dict[str, Any]]) -> list[partial]:
        checks = [
            partial(PostgresWriter._validate_dict_exist, data, "Data"),
            partial(PostgresWriter._validate_dict_not_contains_extra_names, table, data, "Data"),
            partial(PostgresWriter._validate_dict_contains_values_for_not_null_columns, table, data, "Data"),
        ]
        if isinstance(data, list):
            checks.append(partial(PostgresWriter._validate_dict_contains_consistent_keys, data, "Data"))
        return checks

    @staticmethod
    def _validate_update_data_partials(table: Table, update_data: dict[str, Any] | list[dict[str, Any]]) -> list[partial]:
        return [
            partial(PostgresWriter._validate_dict_exist, update_data, "Update data"),
            partial(PostgresWriter._validate_dict_not_contains_extra_names, table, update_data, "Update data"),
            partial(PostgresWriter._validate_dict_not_contains_pk, table, update_data, "Update data"),
        ]

    @staticmethod
    def _validate_conflict_columns_partials(table: Table, conflict_columns: list[str] | None = None) -> list[partial]:
        return [
            partial(PostgresWriter._validate_columns_exist, conflict_columns, "Conflict columns"),
            partial(PostgresWriter._validate_columns_in_table, table, conflict_columns, "Conflict columns"),
            partial(PostgresWriter._validate_columns_unique, table, conflict_columns, "Conflict columns"),
        ]

    @staticmethod
    def _validate_match_partials(table: Table, match: dict[str, Any] | list[dict[str, Any]]) -> list[partial]:
        if isinstance(match, dict):
            columns = list(match.keys())
        else:
            columns = list(match[0].keys())
        checks = [
            partial(PostgresWriter._validate_dict_exist, match, "Match"),
            partial(PostgresWriter._validate_dict_not_contains_extra_names, table, match, "Match"),
            partial(PostgresWriter._validate_columns_unique, table, columns, "Match"),
        ]
        if isinstance(match, list):
            checks.extend([
                partial(PostgresWriter._validate_dict_contains_consistent_keys, match),
                partial(PostgresWriter._validate_match_not_contains_duplicates, match),
            ])
        return checks

    @staticmethod
    def _validate_filter_partials(table: Table, filter: dict[str, Any]) -> list[partial]:
        return [
            partial(PostgresWriter._validate_dict_exist, filter, "Filter"),
            partial(PostgresWriter._validate_columns_in_table, table, list(filter.keys()), "Filter"),
            partial(PostgresWriter._validate_operators_in_filter, filter),
        ]

    @staticmethod
    def _validate_create_operation(table: Table, data: dict[str, Any] | list[dict[str, Any]]) -> None:
        checks = [partial(PostgresWriter._validate_table_has_primary_key, table)]
        checks.extend(PostgresWriter._validate_data_partials(table, data))
        PostgresWriter._run_validation(checks)

    @staticmethod
    def _validate_upsert_operation(
        table: Table,
        data: dict[str, Any] | list[dict[str, Any]],
        conflict_columns: list[str] | None = None,
    ) -> None:
        checks = [partial(PostgresWriter._validate_table_has_primary_key, table)]
        checks.extend(PostgresWriter._validate_data_partials(table, data))
        if conflict_columns:
            checks.extend(PostgresWriter._validate_conflict_columns_partials(table, conflict_columns))
        PostgresWriter._run_validation(checks)

    @staticmethod
    def _validate_update_operation(
        table: Table,
        update_data: dict[str, Any] | list[dict[str, Any]],
        match: dict[str, Any] | list[dict[str, Any]] | None = None,
        filter: dict[str, Any] | None = None,
    ) -> None:
        checks = [partial(PostgresWriter._validate_table_has_primary_key, table)]
        checks.extend(PostgresWriter._validate_update_data_partials(table, update_data))
        if match:
            checks.extend(PostgresWriter._validate_match_partials(table, match))
        if filter:
            checks.extend(PostgresWriter._validate_filter_partials(table, filter))
        PostgresWriter._run_validation(checks)

    @staticmethod
    def _validate_delete_operation(
        table: Table,
        match: dict[str, Any] | list[dict[str, Any]] | None = None,
        filter: dict[str, Any] | None = None,
    ) -> None:
        checks = [partial(PostgresWriter._validate_table_has_primary_key, table)]
        if match:
            checks.extend(PostgresWriter._validate_match_partials(table, match))
        if filter:
            checks.extend(PostgresWriter._validate_filter_partials(table, filter))
        PostgresWriter._run_validation(checks)

    @staticmethod
    def _build_where_conditions(table: Table, filter: dict[str, Any]) -> list:
        conditions = []
        for key, value in filter.items():
            parts = key.split("__")
            col_name = parts[0]
            operator = parts[1] if len(parts) > 1 else "eq"
            column = table.c[col_name]

            if operator == "eq":
                conditions.append(column == value)
            elif operator == "gt":
                conditions.append(column > value)
            elif operator == "lt":
                conditions.append(column < value)
            elif operator == "gte":
                conditions.append(column >= value)
            elif operator == "lte":
                conditions.append(column <= value)
            elif operator == "in":
                if not isinstance(value, list) or not value:
                    raise ValueError(f"IN operator requires non-empty list")
                conditions.append(column.in_(value))
            elif operator == "isnull":
                if value is True:
                    conditions.append(column.is_(None))
                else:
                    conditions.append(column.isnot(None))
            elif operator == "like":
                conditions.append(column.like(value))
            elif operator == "ilike":
                conditions.append(column.ilike(value))
            elif operator == "ne":
                conditions.append(column != value)
            else:
                raise ValueError(f"Unsupported operator '{operator}'")
        return conditions

    async def _get_table(self, table_name: str, schema: str | None = None) -> Table:
        schema = schema or self.default_schema
        cache_key = (schema, table_name)
        if cache_key not in self._tables_cache:
            def load(connection):
                return Table(
                    table_name,
                    self.metadata,
                    autoload_with=connection,
                    keep_existing=True,
                    schema=schema,
                )

            table = await self._client.run_sync_on_connection(load)
            self._tables_cache[cache_key] = table
        return self._tables_cache[cache_key]

    async def write_query(
        self,
        query: str,
        params: dict[str, Any] | list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        self.logger.debug(f"Executing raw write query")
        try:
            self._validate_write_query(query)
            result = await self._client.execute(text(query), params)
            if result.returns_rows:
                rows = result.fetchall()
                self.logger.debug(f"Query returned {len(rows)} rows")
                return [dict(row._mapping) for row in rows]
            self.logger.debug("Query executed successfully, no rows returned")
            return []

        except Exception as e:
            self.logger.error(f"Write query failed: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        self.logger.debug("Closing PostgresWriter client")
        await self._client.close()
        self.logger.debug("PostgresWriter client closed")

    async def create_one(self, table_name: str, data: dict[str, Any], schema: str | None = None) -> dict[str, Any]:
        self.logger.info(f"Creating one record in table '{table_name}'")
        self.logger.debug(
            f"table_name: {truncate(table_name, PostgresWriter.MAX_TABLE_NAME_LENGTH)}, "
            f"data: {truncate(str(data), PostgresWriter.MAX_DATA_LENGTH)}"
        )

        try:
            table = await self._get_table(table_name, schema)
            self._validate_create_operation(table, data)

            pk_columns = list(table.primary_key.columns)
            stmt = (
                insert(table)
                .values(**data)
                .returning(*pk_columns)
            )
            result = await self._client.execute(stmt)
            row = result.fetchone()

            if row is None:
                raise RuntimeError(f"Create returned no primary key for table '{table_name}'")

            pk_value = {col.name: row[col.name] for col in pk_columns}
            self.logger.info(f"Created record with primary key={str(pk_value)} in table '{table_name}'")
            return pk_value

        except Exception as e:
            self.logger.error(f"Failed to create record in '{table_name}': {e}", exc_info=True)
            raise

    async def upsert_one(
        self,
        table_name: str,
        data: dict[str, Any],
        conflict_columns: list[str],
        schema: str | None = None,
    ) -> dict[str, Any]:
        self.logger.info(f"Upserting one record in table '{table_name}'")
        self.logger.debug(
            f"table_name: {truncate(table_name, PostgresWriter.MAX_TABLE_NAME_LENGTH)}, "
            f"data: {truncate(str(data), PostgresWriter.MAX_DATA_LENGTH)}, "
            f"conflict_columns: {truncate(str(conflict_columns), PostgresWriter.MAX_CONFLICT_COLUMNS_LENGTH)}"
        )

        try:
            table = await self._get_table(table_name, schema)
            self._validate_upsert_operation(table, data, conflict_columns)

            pk_columns = list(table.primary_key.columns)
            stmt = insert(table).values(**data)
            update_cols = {k: getattr(stmt.excluded, k) for k in data.keys() if k not in conflict_columns}
            if update_cols:
                stmt = stmt.on_conflict_do_update(
                    index_elements=conflict_columns,
                    set_=update_cols
                ).returning(*pk_columns)
            else:
                stmt = stmt.on_conflict_do_nothing(index_elements=conflict_columns).returning(*pk_columns)
            result = await self._client.execute(stmt)
            row = result.fetchone()

            if row is None:
                raise RuntimeError(f"Upsert returned no primary key for table '{table_name}'")

            pk_value = {col.name: row[col.name] for col in pk_columns}
            self.logger.info(f"Upserted record with primary key={str(pk_value)} in table '{table_name}'")
            return pk_value

        except Exception as e:
            self.logger.error(f"Failed to upsert record in '{table_name}': {e}", exc_info=True)
            raise

    async def update_one(
        self,
        table_name: str,
        update_data: dict[str, Any],
        match: dict[str, Any],
        schema: str | None = None,
    ) -> dict[str, Any]:
        self.logger.info(f"Updating one record in table '{table_name}'")
        self.logger.debug(
            f"table_name: {truncate(table_name, PostgresWriter.MAX_TABLE_NAME_LENGTH)}, "
            f"update_data: {truncate(str(update_data), PostgresWriter.MAX_DATA_LENGTH)}, "
            f"match: '{truncate(str(match), PostgresWriter.MAX_MATCH_LENGTH)}'"
        )

        try:
            table = await self._get_table(table_name, schema)
            self._validate_update_operation(table, update_data, match)

            pk_columns = list(table.primary_key.columns)
            conditions = [table.c[col] == val for col, val in match.items()]
            stmt = (
                update(table)
                .where(*conditions)
                .values(**update_data)
                .returning(*pk_columns)
            )
            result = await self._client.execute(stmt)
            row = result.fetchone()

            if not row:
                raise RuntimeError(f"No matching record found for update in '{table_name}'")

            pk_value = {col.name: row[col.name] for col in pk_columns}
            self.logger.info(f"Updated record with primary key={pk_value} in table '{table_name}'")
            return pk_value

        except Exception as e:
            self.logger.error(f"Failed to update record in '{table_name}': {e}", exc_info=True)
            raise

    async def delete_one(self, table_name: str, match: dict[str, Any], schema: str | None = None) -> dict[str, Any]:
        self.logger.info(f"Deleting one record from table '{table_name}'")
        self.logger.debug(
            f"table_name: {truncate(table_name, PostgresWriter.MAX_TABLE_NAME_LENGTH)}, "
            f"match: '{truncate(str(match), PostgresWriter.MAX_MATCH_LENGTH)}'"
        )

        try:
            table = await self._get_table(table_name, schema)
            self._validate_delete_operation(table, match)

            pk_columns = list(table.primary_key.columns)
            conditions = [table.c[col] == val for col, val in match.items()]
            stmt = (
                delete(table)
                .where(*conditions)
                .returning(*pk_columns)
            )
            result = await self._client.execute(stmt)
            row = result.fetchone()

            if not row:
                raise RuntimeError(f"No matching record found for delete in '{table_name}'")

            pk_value = {col.name: row[col.name] for col in pk_columns}
            self.logger.info(f"Deleted record with primary key={pk_value} from table '{table_name}'")
            return pk_value

        except Exception as e:
            self.logger.error(f"Failed to delete record from '{table_name}': {e}", exc_info=True)
            raise

    async def create_many(
        self,
        table_name: str,
        data_list: list[dict[str, Any]],
        schema: str | None = None,
    ) -> list[dict[str, Any]]:
        self.logger.info(f"Creating {len(data_list)} records in table '{table_name}'")
        self.logger.debug(
            f"table_name: {truncate(table_name, PostgresWriter.MAX_TABLE_NAME_LENGTH)}, "
            f"first item: {truncate(str(data_list[0]), PostgresWriter.MAX_DATA_LENGTH) if data_list else None}"
        )

        try:
            table = await self._get_table(table_name, schema)
            self._validate_create_operation(table, data_list)

            pk_columns = list(table.primary_key.columns)
            stmt = (
                insert(table)
                .values(**data_list[0])
                .returning(*pk_columns)
            )
            result = await self._client.execute(stmt, data_list)
            rows = result.fetchall()

            if len(rows) != len(data_list):
                raise RuntimeError(f"Expected {len(data_list)} rows, got {len(rows)}")

            pk_values = []
            for row in rows:
                pk_dict = {col.name: row[col.name] for col in pk_columns}
                pk_values.append(pk_dict)
            self.logger.info(f"Created {len(pk_values)} records in table '{table_name}'")
            return pk_values

        except Exception as e:
            self.logger.error(f"Failed to create {len(data_list)} records in '{table_name}': {e}", exc_info=True)
            raise

    async def upsert_many(
        self,
        table_name: str,
        data_list: list[dict[str, Any]],
        conflict_columns: list[str],
        schema: str | None = None,
    ) -> list[dict[str, Any]]:
        self.logger.info(f"Upserting {len(data_list)} records in table '{table_name}'")
        self.logger.debug(
            f"table_name: {truncate(table_name, PostgresWriter.MAX_TABLE_NAME_LENGTH)}, "
            f"first item: {truncate(str(data_list[0]), PostgresWriter.MAX_DATA_LENGTH) if data_list else None}, "
            f"conflict_columns: {truncate(str(conflict_columns), PostgresWriter.MAX_CONFLICT_COLUMNS_LENGTH)}"
        )

        try:
            table = await self._get_table(table_name, schema)
            self._validate_upsert_operation(table, data_list, conflict_columns)

            pk_columns = list(table.primary_key.columns)
            stmt = insert(table).values(**data_list[0])
            update_cols = {k: getattr(stmt.excluded, k) for k in data_list[0].keys() if k not in conflict_columns}
            if update_cols:
                stmt = stmt.on_conflict_do_update(
                    index_elements=conflict_columns,
                    set_=update_cols
                ).returning(*pk_columns)
            else:
                stmt = stmt.on_conflict_do_nothing(index_elements=conflict_columns).returning(*pk_columns)
            result = await self._client.execute(stmt, data_list)
            rows = result.fetchall()

            if len(rows) != len(data_list):
                raise RuntimeError(f"Expected {len(data_list)} rows, got {len(rows)}")

            pk_values = []
            for row in rows:
                pk_dict = {col.name: row[col.name] for col in pk_columns}
                pk_values.append(pk_dict)
            self.logger.info(f"Upserted {len(pk_values)} records in table '{table_name}'")
            return pk_values

        except Exception as e:
            self.logger.error(f"Failed to upsert {len(data_list)} records in '{table_name}': {e}", exc_info=True)
            raise

    async def update_many(
        self,
        table_name: str,
        updates: list[SQLUpdate],
        schema: str | None = None
    ) -> list[dict[str, Any]]:
        self.logger.info(f"Updating {len(updates)} records in table '{table_name}'")
        self.logger.debug(
            f"table_name: {truncate(table_name, PostgresWriter.MAX_TABLE_NAME_LENGTH)}, "
            f"first update data: {
                truncate(str(updates[0].update_data), PostgresWriter.MAX_DATA_LENGTH) if updates else None
            }, "
            f"first match: {truncate(str(updates[0].match), PostgresWriter.MAX_MATCH_LENGTH) if updates else None}"
        )

        try:
            table = await self._get_table(table_name, schema)
            data_list = [item.update_data for item in updates]
            match_list = [item.match for item in updates]
            self._validate_update_operation(table, data_list, match_list)

            pk_columns = list(table.primary_key.columns)
            match_columns = list(match_list[0].keys())
            match_tuples = [
                tuple(item.match[col] for col in match_columns)
                for item in updates
            ]
            conditions = tuple_(*[table.c[col] for col in match_columns]).in_(match_tuples)

            update_columns = list(data_list[0].keys())
            case_clauses = {}
            for col in update_columns:
                whens = []
                for item in updates:
                    cond = True
                    for match_col, match_val in item.match.items():
                        cond = cond & (table.c[match_col] == match_val)
                    whens.append((cond, item.update_data[col]))
                case_clauses[col] = case(*whens, else_=table.c[col])

            stmt = (
                update(table)
                .where(conditions)
                .values(**case_clauses)
                .returning(*pk_columns)
            )
            result = await self._client.execute(stmt)
            rows = result.fetchall()

            if len(rows) != len(data_list):
                raise RuntimeError(f"Expected {len(data_list)} rows, got {len(rows)}")

            pk_values = []
            for row in rows:
                pk_dict = {col.name: row[col.name] for col in pk_columns}
                pk_values.append(pk_dict)
            self.logger.info(f"Updated {len(pk_values)} records in table '{table_name}'")
            return pk_values

        except Exception as e:
            self.logger.error(f"Failed to update {len(updates)} records in '{table_name}': {e}", exc_info=True)
            raise

    async def update_by_filter(
        self,
        table_name: str,
        update_data: dict[str, Any],
        filter: dict[str, Any],
        schema: str | None = None,
    ) -> list[dict[str, Any]]:
        self.logger.info(f"Updating records in table '{table_name}' by filter")
        self.logger.debug(
            f"table_name: {truncate(table_name, PostgresWriter.MAX_TABLE_NAME_LENGTH)}, "
            f"update_data: {truncate(str(update_data), PostgresWriter.MAX_DATA_LENGTH)}, "
            f"filter: {truncate(str(filter), PostgresWriter.MAX_FILTER_LENGTH)}"
        )

        try:
            table = await self._get_table(table_name, schema)
            self._validate_update_operation(table, update_data, filter=filter)

            pk_columns = list(table.primary_key.columns)
            conditions = self._build_where_conditions(table, filter)
            stmt = (
                update(table)
                .where(*conditions)
                .values(**update_data)
                .returning(*pk_columns)
            )
            result = await self._client.execute(stmt)
            rows = result.fetchall()

            if not rows:
                raise RuntimeError(f"No matching records found for update by filter in '{table_name}'")

            pk_values = []
            for row in rows:
                pk_dict = {col.name: row[col.name] for col in pk_columns}
                pk_values.append(pk_dict)
            self.logger.info(f"Updated {len(pk_values)} records in table '{table_name}' by filter")
            return pk_values

        except Exception as e:
            self.logger.error(f"Failed to update records by filter in '{table_name}': {e}", exc_info=True)
            raise

    async def delete_many(
        self,
        table_name: str,
        match_list: list[dict[str, Any]],
        schema: str | None = None,
    ) -> list[dict[str, Any]]:
        self.logger.info(f"Deleting {len(match_list)} records from table '{table_name}'")
        self.logger.debug(
            f"table_name: {truncate(table_name, PostgresWriter.MAX_TABLE_NAME_LENGTH)}, "
            f"first match item='{truncate(str(match_list[0]), PostgresWriter.MAX_MATCH_LENGTH) if match_list else None}'"
        )

        try:
            table = await self._get_table(table_name, schema)
            self._validate_delete_operation(table, match_list)

            pk_columns = list(table.primary_key.columns)
            match_columns = list(match_list[0].keys())
            match_tuples = [
                tuple(item[col] for col in match_columns)
                for item in match_list
            ]
            conditions = tuple_(*[table.c[col] for col in match_columns]).in_(match_tuples)
            stmt = (
                delete(table)
                .where(conditions)
                .returning(*pk_columns)
            )
            result = await self._client.execute(stmt)
            rows = result.fetchall()

            if len(rows) != len(match_list):
                raise RuntimeError(f"Expected {len(match_list)} rows, got {len(rows)}")

            pk_values = []
            for row in rows:
                pk_dict = {col.name: row[col.name] for col in pk_columns}
                pk_values.append(pk_dict)
            self.logger.info(f"Deleted {len(pk_values)} records from table '{table_name}'")
            return pk_values

        except Exception as e:
            self.logger.error(f"Failed to delete {len(match_list)} records from '{table_name}': {e}", exc_info=True)
            raise

    async def delete_by_filter(
        self,
        table_name: str,
        filter: dict[str, Any],
        schema: str | None = None,
    ) -> list[dict[str, Any]]:
        self.logger.info(f"Deleting records from table '{table_name}' by filter")
        filter_str = str(filter)
        self.logger.debug(f"filter: {truncate(filter_str, PostgresWriter.MAX_FILTER_LENGTH)}")

        try:
            table = await self._get_table(table_name, schema)
            self._validate_delete_operation(table, filter=filter)

            pk_columns = list(table.primary_key.columns)
            conditions = self._build_where_conditions(table, filter)
            stmt = (
                delete(table)
                .where(*conditions)
                .returning(*pk_columns)
            )
            result = await self._client.execute(stmt)
            rows = result.fetchall()

            if not rows:
                raise RuntimeError(f"No matching records found for delete by filter in '{table_name}'")

            pk_values = []
            for row in rows:
                pk_dict = {col.name: row[col.name] for col in pk_columns}
                pk_values.append(pk_dict)
            self.logger.info(f"Deleted {len(pk_values)} records from table '{table_name}' by filter")
            return pk_values

        except Exception as e:
            self.logger.error(f"Failed to delete records by filter from '{table_name}': {e}", exc_info=True)
            raise

    def table_cache_clear(self) -> None:
        self._tables_cache.clear()

    def invalidate_table_cache(self, table_name: str, schema: str | None = None) -> None:
        schema = schema or self.default_schema
        self._tables_cache.pop((schema, table_name), None)
