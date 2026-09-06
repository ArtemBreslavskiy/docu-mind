import asyncio
from logging import Logger
from src.core.chunkers.base import Chunk
from src.data.db.base import SemanticSearchResult
from src.data.db.filter import FilterCondition, FilterGroup
from src.data.db.nosql.vector.base import IVectorReader
from src.utils.qdrant_utils import convert_filter
from src.data.db.nosql.vector.qdrant.client import MyQdrantClient


class QdrantReader(IVectorReader):
    def __init__(
        self,
        client: MyQdrantClient,
        collection_name: str,
        logger: Logger | None = None,
    ):
        self._client = client
        self.logger = logger if logger else client.logger
        self.collection_name = collection_name

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter: FilterCondition | FilterGroup | None = None,
    ) -> list[SemanticSearchResult]:
        self.logger.debug(f"Searching for top {top_k} vectors in collection '{self.collection_name}'")
        qfilter = convert_filter(filter) if filter else None

        try:
            search_result = self._client.engine.query_points(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=qfilter,
                with_payload=True,
                with_vectors=False,
            )
        except Exception as e:
            self.logger.error(f"Search failed: {e}", exc_info=True)
            raise

        results = []
        for scored_point in search_result:
            payload = scored_point.payload or {}
            chunk = Chunk(
                id=str(scored_point.id),
                text=payload.get("text", ""),
                metadata=payload.get("metadata", {}),
            )
            results.append(
                SemanticSearchResult(
                    id=str(scored_point.id),
                    chunk=chunk,
                    score=scored_point.score,
                )
            )

        self.logger.debug(f"Found {len(results)} results")
        return results

    async def get_schema_info(self) -> str:
        try:
            collection_info = await asyncio.to_thread(
                self._client.engine.get_collection, self.collection_name
            )
            status = collection_info.status
            vectors_count = collection_info.vectors_count
            points_count = collection_info.points_count
            vector_size = collection_info.config.params.vectors.size if collection_info.config.params.vectors else "unknown"
            return (
                f"Qdrant collection: name='{self.collection_name}', "
                f"status={status}, points_count={points_count}, "
                f"vectors_count={vectors_count}, vector_size={vector_size}"
            )
        except Exception as e:
            self.logger.error(f"Failed to get schema info: {e}")
            return f"Error getting schema info for collection '{self.collection_name}': {e}"

    async def connect(self) -> None:
        await self._client.connect()

    async def close(self) -> None:
        await self._client.close()

    async def ping(self) -> bool:
        return await self._client.ping()
