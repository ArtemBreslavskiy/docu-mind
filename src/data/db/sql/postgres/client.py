from logging import Logger
from typing import Any, Callable
from sqlalchemy import Executable
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine
from sqlalchemy import text
from src.data.db.base import IConnection, ITransactional
from sqlalchemy.engine import Result
from src.utils.truncate import truncate
from src.utils.logger_setup import get_null_logger


class PostgresAsyncClient(IConnection, ITransactional):
    MAX_SQL_REQUEST_LENGTH_TO_LOG = 500
    MAX_SQL_PARAMS_LENGTH_TO_LOG = 500

    def __init__(
        self,
        url: str | None = None,
        engine: AsyncEngine | None = None,
        logger: Logger | None = None,
        **kwargs
    ):
        self.logger = logger if logger else get_null_logger()
        if url is None and engine is None:
            msg = "Either 'url' or 'engine' must be provided."
            self.logger.error(msg)
            raise ValueError(msg)
        elif url is not None and engine is not None:
            msg = "Provide either 'url' or 'engine', not both."
            self.logger.error("Provide either 'url' or 'engine', not both.")
            raise ValueError(msg)

        super().__init__(**kwargs)
        if engine is not None:
            self.engine = engine
            self._owns_engine = False
        else:
            self.engine = create_async_engine(url, echo=False, pool_pre_ping=True)
            self._owns_engine = True
        self._conn: AsyncConnection | None = None
        self._in_tx: bool = False

    async def connect(self) -> None:
        self.logger.debug("Connecting to Postgres...")
        if self._conn is not None:
            self.logger.debug("Connection already exist, reusing")
            return
        self.logger.debug("Creating connection")
        try:
            self._conn = await self.engine.connect()
        except Exception as e:
            self.logger.error(f"Failed to establish database connection: {e}", exc_info=True)
            raise
        self.logger.debug("Connection established")

    async def close(self) -> None:
        self.logger.debug("Closing PostgresAsyncClient...")
        error_lines = []
        closed_connection = False
        disposed_engine = False

        if self._conn is not None:
            try:
                await self._conn.close()
            except Exception as e:
                self.logger.error(f"Error while closing connection: {e}", exc_info=True)
                error_lines.append(str(e))
            finally:
                self._conn = None
            closed_connection = True
            self.logger.debug("Closed active database connection")
        else:
            self.logger.debug("No active connection to close")

        if self._owns_engine and self.engine is not None:
            try:
                await self.engine.dispose()
            except Exception as e:
                self.logger.error(f"Error while disposing engine: {e}", exc_info=True)
                error_lines.append(str(e))
            finally:
                self.engine = None
            disposed_engine = True
            self.logger.debug("Disposed owned async engine")
        else:
            self.logger.debug("Engine is not owned, skipping disposal")

        if closed_connection or disposed_engine:
            self.logger.info("PostgresAsyncClient resources released successfully")
        else:
            self.logger.info("PostgresAsyncClient closed (no resources to release)")

        if error_lines:
            raise RuntimeError("\n".join(error_lines))

    async def ping(self) -> bool:
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            self.logger.error(f"Ping failed: {e}", exc_info=True)
            return False

    async def begin_transaction(self) -> None:
        if self._in_tx:
            raise RuntimeError("Transaction already in progress")

        if self._conn is not None:
            self.logger.debug("Using existing connection for transaction")
        else:
            await self.connect()
            self.logger.debug("New connection for transaction")
        self._in_tx = True

    async def commit_transaction(self) -> None:
        self.logger.debug("Committing transaction...")
        if self._conn is None:
            raise RuntimeError("No active transaction")

        try:
            await self._conn.commit()
            self.logger.debug("Transaction committed successfully")
        except Exception as e:
            self.logger.error(f"Commit failed: {e}", exc_info=True)
            raise
        finally:
            self._in_tx = False

    async def rollback_transaction(self) -> None:
        self.logger.debug("Rolling back transaction...")
        if self._conn is None:
            raise RuntimeError("No active transaction")

        try:
            await self._conn.rollback()
            self.logger.debug("Transaction rolled back successfully")
        except Exception as e:
            self.logger.error(f"Failed to rollback transaction: {e}", exc_info=True)
            raise
        finally:
            self._in_tx = False

    async def execute(
        self,
        stmt: Executable,
        params: dict[str, Any] | list[dict[str, Any]] | None = None,
    ) -> Result:
        sql_str = str(stmt)
        self.logger.debug(f"Executing SQL: {truncate(sql_str, PostgresAsyncClient.MAX_SQL_REQUEST_LENGTH_TO_LOG)}")
        if params:
            params_str = str(params)
            self.logger.debug(f"Params: {truncate(params_str, PostgresAsyncClient.MAX_SQL_PARAMS_LENGTH_TO_LOG)}")
        error_lines = []

        await self.connect()
        try:
            result = await self._conn.execute(stmt, params or {})
            if not self._in_tx:
                await self._conn.commit()
            if result.returns_rows:
                self.logger.debug(f"SQL executed successfully, returned rows")
            else:
                self.logger.debug("SQL executed successfully (no rows returned)")
            return result

        except Exception as e:
            self.logger.error(f"SQL execution failed: {e}", exc_info=True)
            error_lines.append(str(e))
            if not self._in_tx:
                try:
                    await self._conn.rollback()
                    self.logger.debug("Transaction rolled back successfully")
                except Exception as e:
                    self.logger.error(f"Failed to rollback transaction: {e}", exc_info=True)
                    error_lines.append(str(e))

    async def run_sync_on_connection(self, func: Callable, *args, **kwargs) -> Any:
        func_name = getattr(func, '__name__', str(func))
        self.logger.debug(f"Running sync function '{func_name}' on connection")
        error_lines = []

        await self.connect()
        try:
            result = await self._conn.run_sync(func, *args, **kwargs)
            self.logger.debug(f"Sync function '{func_name}' executed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Sync function '{func_name}' failed: {e}", exc_info=True)
            error_lines.append(str(e))
            if not self._in_tx:
                try:
                    await self._conn.rollback()
                    self.logger.debug("Transaction rolled back successfully")
                except Exception as e:
                    self.logger.error(f"Failed to rollback transaction: {e}", exc_info=True)
                    error_lines.append(str(e))
