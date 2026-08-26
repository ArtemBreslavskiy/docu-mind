from typing import Any
from logging import Logger
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession, AsyncTransaction, Query
from src.data.db.base import IConnection, ITransactional
from src.utils.logger_setup import get_null_logger
from src.utils.truncate import truncate


class Neo4jAsyncClient(IConnection, ITransactional):
    MAX_CYPHER_REQUEST_LENGTH_TO_LOG = 500
    MAX_CYPHER_PARAMS_LENGTH_TO_LOG = 500

    def __init__(
        self,
        url: str | None = None,
        driver: AsyncDriver | None = None,
        logger: Logger | None = None,
        **kwargs
    ):
        self.logger = logger if logger else get_null_logger()
        if url is None and driver is None:
            msg = "Either 'url' or 'driver' must be provided."
            self.logger.error(msg)
            raise ValueError(msg)
        elif url is not None and driver is not None:
            msg = "Provide either 'url' or 'driver', not both."
            self.logger.error(msg)
            raise ValueError(msg)

        super().__init__(**kwargs)
        if driver is not None:
            self._driver = driver
            self._owns_driver = False
        else:
            self._driver = AsyncGraphDatabase.driver(url, auth=None)
            self._owns_driver = True
        self._session: AsyncSession | None = None
        self._tx: AsyncTransaction | None = None
        self._in_tx: bool = False

    async def connect(self) -> None:
        self.logger.debug("Connecting to Neo4j...")
        if self._session is not None:
            self.logger.debug("Session already exist, reusing")
            return
        self.logger.debug("Creating session")
        try:
            self._session = self._driver.session()
        except Exception as e:
            self.logger.error(f"Failed to create a new Neo4j session: {e}", exc_info=True)
            raise
        self._tx = None
        self.logger.debug("Session created successfully")

    async def _get_transaction(self, session: AsyncSession) -> AsyncTransaction:
        if self._tx is not None:
            return self._tx
        self.logger.debug("Creating transaction")
        try:
            tx = await session.begin_transaction()
            self.logger.debug("Transaction created successfully")
            return tx
        except Exception as e:
            self.logger.error(f"Failed to begin a new Neo4j transaction: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        self.logger.debug("Closing Neo4jAsyncClient...")
        error_lines = []
        closed_tx = False
        closed_session = False
        closed_driver = False

        if self._tx is not None:
            try:
                await self._tx.close()
            except Exception as e:
                self.logger.error(f"Error while closing transaction: {e}", exc_info=True)
                error_lines.append(str(e))
            finally:
                self._tx = None
            closed_tx = True
            self.logger.debug("Closed active database transaction")
        else:
            self.logger.debug("No active transaction to close")

        if self._session is not None:
            try:
                await self._session.close()
            except Exception as e:
                self.logger.error(f"Error while closing session: {e}", exc_info=True)
                error_lines.append(str(e))
            finally:
                self._session = None
            closed_session = True
            self.logger.debug("Closed active database session")
        else:
            self.logger.debug("No active session to close")

        if self._owns_driver and self._driver is not None:
            try:
                await self._driver.close()
            except Exception as e:
                self.logger.error(f"Error while closing driver: {e}", exc_info=True)
                error_lines.append(str(e))
            finally:
                self._driver = None
            closed_driver = True
            self.logger.debug("Disposed owned async driver")
        else:
            self.logger.debug("Driver is not owned, skipping disposal")

        if closed_tx or closed_session or closed_driver:
            self.logger.info("Neo4jAsyncClient resources released successfully")
        else:
            self.logger.info("Neo4jAsyncClient closed (no resources to release)")

        if error_lines:
            raise RuntimeError("\n".join(error_lines))

    async def ping(self) -> bool:
        try:
            async with self._driver.session() as session:
                await session.run("RETURN 1")
            return True
        except Exception as e:
            self.logger.error(f"Ping failed: {e}", exc_info=True)
            return False

    async def begin_transaction(self) -> None:
        if self._in_tx:
            raise RuntimeError("Transaction already in progress")

        if self._session is not None:
            self.logger.debug("Using existing session for transaction")
        else:
            await self.connect()
            self.logger.debug("New session for transaction")
        self._tx = await self._get_transaction(self._session)
        self._in_tx = True
        self.logger.debug("Transaction explicitly started")

    async def commit_transaction(self) -> None:
        self.logger.debug("Committing transaction...")
        if self._tx is None:
            raise RuntimeError("No active transaction")

        try:
            await self._tx.commit()
            self.logger.debug("Transaction committed successfully")
        except Exception as e:
            self.logger.error(f"Commit failed: {e}", exc_info=True)
            raise
        finally:
            self._tx = None
            self._in_tx = False

    async def rollback_transaction(self) -> None:
        self.logger.debug("Rolling back transaction...")
        if self._tx is None:
            raise RuntimeError("No active transaction")

        try:
            await self._tx.rollback()
            self.logger.debug("Transaction rolled back successfully")
        except Exception as e:
            self.logger.error(f"Failed to rollback transaction: {e}", exc_info=True)
            raise
        finally:
            self._tx = None
            self._in_tx = False

    async def execute(
        self,
        query: str,
        params: dict | list[dict] | None = None,
        returning: bool = True
    ) -> list[dict]:
        self.logger.debug(f"Executing Cypher: {truncate(query, Neo4jAsyncClient.MAX_CYPHER_REQUEST_LENGTH_TO_LOG)}")
        if params:
            params_str = str(params)
            self.logger.debug(f"Params: {truncate(params_str, Neo4jAsyncClient.MAX_CYPHER_PARAMS_LENGTH_TO_LOG)}")
        error_lines = []

        await self.connect()
        tx = await self._get_transaction(self._session)
        try:
            result = await tx.run(Query(query), params or {})
            records = [record.data for record in await result.fetch()] if returning else []
            if records:
                self.logger.debug(f"Cypher executed successfully, returned {len(records)} records")
            else:
                self.logger.debug("Cypher executed successfully (no records returned)")
            if not self._in_tx:
                await tx.commit()
            return records

        except Exception as e:
            self.logger.error(f"Cypher execution failed: {e}", exc_info=True)
            error_lines.append(str(e))
            if not self._in_tx:
                try:
                    await tx.rollback()
                except Exception as e:
                    self.logger.error(f"Rollback failed: {e}", exc_info=True)
                    error_lines.append(str(e))

        finally:
            if not self._in_tx:
                try:
                    await tx.close()
                except Exception as e:
                    self.logger.error(f"Error while closing transaction: {e}", exc_info=True)
                    error_lines.append(str(e))

        if error_lines:
            raise RuntimeError("\n".join(error_lines))
