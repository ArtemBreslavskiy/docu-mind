import asyncio
from logging import Logger
from qdrant_client import QdrantClient
from src.data.db.base import IConnection
from src.utils.logger_setup import get_null_logger


class MyQdrantClient(IConnection):
    def __init__(
        self,
        host: str,
        port: int,
        api_key: str | None = None,
        prefer_grpc: bool = False,
        timeout: int = 30,
        logger: Logger | None = None
    ):
        self.logger = logger if logger else get_null_logger()
        self.host = host
        self.port = port
        self.api_key = api_key
        self.prefer_grpc = prefer_grpc
        self.timeout = timeout
        self.engine: QdrantClient | None = None

    async def connect(self) -> None:
        self.logger.debug("Connecting to Qdrant...")
        if self.engine is not None:
            self.logger.debug("Connection already established, reusing")
            return

        def _create_client():
            self.logger.debug("Creating Qdrant client instance")
            return QdrantClient(
                host=self.host,
                port=self.port,
                api_key=self.api_key,
                prefer_grpc=self.prefer_grpc,
                timeout=self.timeout,
            )

        try:
            self.engine = await asyncio.to_thread(_create_client)
            self.logger.info("Qdrant client created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create Qdrant client: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        self.logger.debug("Closing Qdrant client...")
        if self.engine is None:
            self.logger.debug("No active client to close")
            return

        try:
            self.engine.close()
            self.logger.debug("Qdrant client closed successfully")
        except Exception as e:
            self.logger.error(f"Error while closing Qdrant client: {e}", exc_info=True)
            raise
        finally:
            self.engine = None

    async def ping(self) -> bool:
        self.logger.debug("Pinging Qdrant server...")
        if self.engine is None:
            self.logger.warning("Ping attempted but client is not connected")
            return False

        try:
            def _ping():
                self.engine.get_collections()
                return True

            result = await asyncio.to_thread(_ping)
            self.logger.debug("Ping successful")
            return result
        except Exception as e:
            self.logger.error(f"Ping failed: {e}", exc_info=True)
            return False
