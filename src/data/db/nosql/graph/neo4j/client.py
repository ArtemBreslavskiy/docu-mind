from typing import Any
from logging import Logger
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession, AsyncTransaction, Query
from src.data.db.base import BaseDBTransactionManager
from src.utils.logger_setup import get_null_logger
from src.utils.truncate import truncate


class Neo4jAsyncClient(BaseDBTransactionManager):
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

    async def _get_session(self) -> AsyncSession:
        if self._session is not None:
            return self._session
        try:
            return self._driver.session()
        except Exception as e:
            self.logger.error(f"Failed to create a new Neo4j session: {e}", exc_info=True)
            raise

    async def _get_transaction(self, session: AsyncSession) -> AsyncTransaction:
        if self._tx is not None:
            return self._tx
        try:
            return await session.begin_transaction()
        except Exception as e:
            self.logger.error(f"Failed to begin a new Neo4j transaction: {e}", exc_info=True)
            raise

    async def execute(
        self,
        query: str,
        params: dict[str, Any] | list[dict[str, Any]] | None = None,
        returning: bool = True
    ) -> list[dict[str, Any]]:
        self.logger.debug(f"Executing Cypher: {truncate(query, Neo4jAsyncClient.MAX_CYPHER_REQUEST_LENGTH_TO_LOG)}")
        if params:
            params_str = str(params)
            self.logger.debug(f"Params: {truncate(params_str, Neo4jAsyncClient.MAX_CYPHER_PARAMS_LENGTH_TO_LOG)}")
        error_lines = []

        try:
            session = await self._get_session()
            tx = await self._get_transaction(session)
            result = await tx.run(Query(query), params or {})
            records = [record.data for record in await result.fetch()] if returning else []
            if records:
                self.logger.debug(f"Cypher executed successfully, returned {len(records)} records")
            else:
                self.logger.debug("Cypher executed successfully (no records returned)")
            if self._tx is None:
                await tx.commit()
            return records

        except Exception as e:
            self.logger.error(f"Cypher execution failed: {e}", exc_info=True)
            error_lines.append(str(e))
            if self._tx is None:
                try:
                    await tx.rollback()
                except Exception as e:
                    self.logger.error(f"Rollback failed: {e}", exc_info=True)
                    error_lines.append(str(e))

        finally:
            if self._tx is None:
                try:
                    await tx.close()
                except Exception as e:
                    self.logger.error(f"Error while closing transaction: {e}", exc_info=True)
                    error_lines.append(str(e))

            if self._session is None:
                try:
                    await session.close()
                except Exception as e:
                    self.logger.error(f"Error while closing session: {e}", exc_info=True)
                    error_lines.append(str(e))

        if error_lines:
            raise RuntimeError("\n".join(error_lines))

    async def begin_transaction(self) -> None:
        self.logger.debug("Starting transaction...")
        try:
            if self._session is not None or self._tx is not None:
                raise RuntimeError("Transaction already started")
            self._session = self._driver.session()
            self.logger.debug("Session started successfully")
            self._tx = await self._session.begin_transaction()
            self.logger.debug("Transaction started successfully")

        except Exception as e:
            self.logger.error(f"Failed to begin transaction: {e}", exc_info=True)
            raise

    async def commit_transaction(self) -> None:
        self.logger.debug("Committing transaction...")
        if self._tx is None:
            raise RuntimeError("No active transaction")
        error_lines = []

        try:
            await self._tx.commit()
            self.logger.debug("Transaction committed successfully")

        except Exception as e:
            self.logger.error(f"Commit failed: {e}", exc_info=True)
            error_lines.append(str(e))

        finally:
            self._tx = None
            try:
                await self._session.close()
            except Exception as e:
                self.logger.error(f"Error while closing session after transaction commit: {e}", exc_info=True)
                error_lines.append(str(e))
            finally:
                self._session = None

        if error_lines:
            raise RuntimeError("\n".join(error_lines))

    async def rollback_transaction(self) -> None:
        self.logger.debug("Rolling back transaction...")
        if self._tx is None:
            raise RuntimeError("No active transaction")
        error_lines = []

        try:
            await self._tx.rollback()
            self.logger.debug("Transaction rolled back successfully")

        except Exception as e:
            self.logger.error(f"Failed to rollback transaction: {e}", exc_info=True)
            error_lines.append(str(e))

        finally:
            self._tx = None
            try:
                await self._session.close()
            except Exception as e:
                self.logger.error(f"Error while closing session after transaction rollback: {e}", exc_info=True)
                error_lines.append(str(e))
            finally:
                self._session = None

        if error_lines:
            raise RuntimeError("\n".join(error_lines))

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
