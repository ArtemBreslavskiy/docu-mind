import uuid
from logging import Logger
from qdrant_client import models
from functools import partial
from src.utils.truncate import truncate
from src.data.db.filter import FilterCondition, FilterGroup
from src.data.db.nosql.vector.base import IVectorWriter, VectorAdd, VectorUpdate
from src.utils.logger_setup import get_null_logger
from src.utils.qdrant_utils import convert_filter, build_should_filter
from src.data.db.nosql.vector.qdrant.client import MyQdrantClient
from src.utils.db_utils import (
    validate_strings_exist,
    validate_dict_exist,
    validate_dict_contains_consistent_keys,
    validate_all_conflict_properties_in_properties,
    validate_match_not_contains_duplicates,
    validate_filter_exist
)


class QdrantWriter(IVectorWriter):
    DISTANCE_MAP = {
        "Cosine": models.Distance.COSINE,
        "Euclid": models.Distance.EUCLID,
        "Dot": models.Distance.DOT,
    }
    MAX_VALIDATION_ERRORS = 20
    LOG_MAX_VECTOR_LENGTH = 500
    LOG_MAX_CREATE_METADATA_LENGTH = 500
    LOG_MAX_UPSERT_METADATA_LENGTH = 500
    LOG_MAX_UPDATE_METADATA_LENGTH = 500
    LOG_MAX_CONFLICT_PROPERTIES_LENGTH = 500
    LOG_MAX_MATCH_LENGTH = 500
    LOG_MAX_FILTER_LENGTH = 500

    def __init__(
        self,
        client: MyQdrantClient,
        collection_name: str,
        vector_size: int,
        distance: str = "cosine",
        recreate_collection: bool = False,
        scroll_limit: int = 1000,
        batch_size: int = 1000,
        logger: Logger | None = None,
    ):
        self._client = client
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance = distance
        self.recreate_collection = recreate_collection
        self.scroll_limit = scroll_limit
        self.batch_size = batch_size
        self.logger = logger if logger else client.logger

        self._ensure_collection(recreate=self.recreate_collection)

    @staticmethod
    def _validate_strings_exist(strings: str | list[str], context: str = "") -> str | None:
        return validate_strings_exist(strings, context, QdrantWriter.MAX_VALIDATION_ERRORS, True)

    @staticmethod
    def _validate_dict_exist(data: dict | list[dict], context: str = "") -> str | None:
        return validate_dict_exist(data, context, QdrantWriter.MAX_VALIDATION_ERRORS, True)

    @staticmethod
    def _validate_dict_contains_consistent_keys(data_list: list[dict], context: str = "") -> str | None:
        return validate_dict_contains_consistent_keys(data_list, context, QdrantWriter.MAX_VALIDATION_ERRORS, True)

    @staticmethod
    def _validate_all_conflict_properties_in_properties(
        properties: dict | list[dict],
        conflict_properties: list[str]
    ) -> str | None:
        return validate_all_conflict_properties_in_properties(
            properties,
            conflict_properties,
            QdrantWriter.MAX_VALIDATION_ERRORS,
            True
        )

    @staticmethod
    def _validate_match_not_contains_duplicates(match: list[dict]) -> str | None:
        return validate_match_not_contains_duplicates(match, QdrantWriter.MAX_VALIDATION_ERRORS, True)

    @staticmethod
    def _validate_filter_exist(filter: FilterCondition | FilterGroup) -> str | None:
        return validate_filter_exist(filter, QdrantWriter.MAX_VALIDATION_ERRORS, return_str=True)

    @staticmethod
    def _validate_vector(vector: list[float] | list[list[float]], expected_size: int) -> str | None:
        if not vector:
            return "[Vector] Vector cannot be empty."

        if isinstance(vector[0], list):
            error_lines = []
            for i, vec in enumerate(vector):
                if len(vec) != expected_size:
                    error_lines.append(
                        f"[Item {i}] Vector length {len(vec)}, expected {expected_size}"
                    )
            if error_lines:
                return "[Vector] Validation errors:\n" + "\n".join(error_lines)
        else:
            if len(vector) != expected_size:
                return f"[Vector] Vector length {len(vector)}, expected {expected_size}"

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
    def _validate_conflict_properties_partials(conflict_properties: list[str]) -> list[partial]:
        return [partial(QdrantWriter._validate_strings_exist, conflict_properties, "Conflict properties")]

    @staticmethod
    def _validate_match_partials(match: dict | list[dict]) -> list[partial]:
        checks = [partial(QdrantWriter._validate_dict_exist, match, "Match")]
        if isinstance(match, list):
            checks.append(partial(QdrantWriter._validate_match_not_contains_duplicates, match))
        return checks

    @staticmethod
    def _validate_filter_partials(filter: FilterCondition | FilterGroup):
        return [partial(QdrantWriter._validate_filter_exist, filter)]

    def _validate_create_operation(self, vector: list[float] | list[list[float]], metadata: dict | list[dict]) -> None:
        checks = [
            partial(QdrantWriter._validate_vector, vector, self.vector_size),
            partial(QdrantWriter._validate_dict_exist, metadata, "Metadata"),
        ]
        if isinstance(metadata, list):
            checks.append(partial(QdrantWriter._validate_dict_contains_consistent_keys, metadata, "Metadata"))
        QdrantWriter._run_validation(checks)

    def _validate_upsert_operation(
        self,
        vector: list[float] | list[list[float]],
        metadata: dict | list[dict],
        conflict_properties: list[str]
    ) -> None:
        checks = [
            partial(QdrantWriter._validate_vector, vector, self.vector_size),
            partial(QdrantWriter._validate_dict_exist, metadata, "Metadata"),
        ]
        if isinstance(metadata, list):
            checks.append(partial(QdrantWriter._validate_dict_contains_consistent_keys, metadata, "Metadata"))
        checks.append(partial(
            QdrantWriter._validate_all_conflict_properties_in_properties,
            metadata,
            conflict_properties
        ))
        checks.extend(QdrantWriter._validate_conflict_properties_partials(conflict_properties))
        QdrantWriter._run_validation(checks)

    def _validate_update_operation(
        self,
        vector: list[float] | list[list[float]] | None = None,
        metadata: dict | list[dict] | None = None,
        match: dict | list[dict] | None = None,
        filter: FilterCondition | FilterGroup | None = None,
    ) -> None:
        checks = []
        if vector:
            checks.append(partial(QdrantWriter._validate_vector, vector, self.vector_size))
        if metadata:
            checks.append(partial(QdrantWriter._validate_dict_exist, metadata, "Metadata"))
            if isinstance(metadata, list):
                checks.append(partial(QdrantWriter._validate_dict_contains_consistent_keys, metadata, "Metadata"))
        if match:
            checks.extend(QdrantWriter._validate_match_partials(match))
        if filter:
            checks.extend(QdrantWriter._validate_filter_partials(filter))
        if checks:
            QdrantWriter._run_validation(checks)

    @staticmethod
    def _validate_delete_operation(
        match: dict | list[dict] | None = None,
        filter: FilterCondition | FilterGroup | None = None,
    ) -> None:
        checks = []
        if match:
            checks.extend(QdrantWriter._validate_match_partials(match))
        if filter:
            checks.extend(QdrantWriter._validate_filter_partials(filter))
        if checks:
            QdrantWriter._run_validation(checks)

    def _ensure_collection(self, recreate: bool = False):
        collections = self._client.engine.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if exists and recreate:
            self._client.engine.delete_collection(self.collection_name)
            exists = False
            self.logger.info(f"Recreated collection '{self.collection_name}'")

        if not exists:
            distance_enum = self.DISTANCE_MAP.get(self.distance, models.Distance.COSINE)

            self._client.engine.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=self.vector_size, distance=distance_enum)
            )
        self.logger.info(f"Created collection '{self.collection_name}' with size {self.vector_size}")

    def _find_points_by_match(self, match: dict) -> list[str]:
        filter = models.Filter(
            must=[
                models.FieldCondition(
                    key=k,
                    match=models.MatchValue(value=v),
                )
                for k, v in match.items()
            ]
        )
        ids = []
        offset = None
        while True:
            points, next_offset = self._client.engine.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter,
                limit=self.scroll_limit,
                offset=offset,
                with_payload=False,
                with_vectors=False,
            )
            ids.extend([p.id for p in points])
            if not next_offset:
                break
            offset = next_offset
        return ids

    def _find_all_points_by_filter(self, filter: FilterCondition | FilterGroup) -> list[str]:
        qfilter = convert_filter(filter)
        ids = []
        offset = None
        while True:
            points, next_offset = self._client.engine.scroll(
                collection_name=self.collection_name,
                scroll_filter=qfilter,
                limit=self.scroll_limit,
                offset=offset,
                with_payload=False,
                with_vectors=False,
            )
            ids.extend([p.id for p in points])
            if not next_offset:
                break
            offset = next_offset
        return ids

    async def create_one(self, vector: list[float], metadata: dict) -> str:
        self.logger.info(f"Creating one point...")
        self.logger.debug(
            f"update vector: {truncate(str(vector), QdrantWriter.LOG_MAX_VECTOR_LENGTH)}, "
            f"update metadata: {truncate(str(metadata), QdrantWriter.LOG_MAX_CREATE_METADATA_LENGTH)}"
        )
        try:
            self._validate_create_operation(vector, metadata)

            point_id = str(uuid.uuid4())
            self._client.engine.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=metadata,
                    )
                ],
            )
            self.logger.info(f"Created point {point_id}")
            return point_id

        except Exception as e:
            self.logger.error(f"Failed to create point: {e}", exc_info=True)
            raise

    async def upsert_one(
        self,
        upsert_vector: list[float],
        upsert_metadata: dict,
        conflict_properties: list[str],
    ) -> str:
        self.logger.info(f"Upserting one point...")
        self.logger.debug(
            f"update vector: {truncate(str(upsert_vector), QdrantWriter.LOG_MAX_VECTOR_LENGTH) if upsert_vector else None}, "
            f"update metadata: {truncate(str(upsert_metadata), QdrantWriter.LOG_MAX_UPSERT_METADATA_LENGTH) if upsert_metadata else None}, "
            f"conflict properties: {truncate(str(conflict_properties), QdrantWriter.LOG_MAX_CONFLICT_PROPERTIES_LENGTH)}"
        )
        try:
            self._validate_upsert_operation(upsert_vector, upsert_metadata, conflict_properties)

            match = {prop: upsert_metadata.get(prop) for prop in conflict_properties}
            existing_ids = self._find_points_by_match(match)
            if existing_ids:
                if len(existing_ids) > 1:
                    self.logger.warning(f"Found {len(existing_ids)} points for match, using first one")
                point_id = str(existing_ids[0])
                self._client.engine.upsert(
                    collection_name=self.collection_name,
                    points=[
                        models.PointStruct(
                            id=point_id,
                            vector=upsert_vector,
                            payload=upsert_metadata,
                        )
                    ],
                )
                self.logger.info(f"Upserted (updated) point {point_id}")
                return point_id

            else:
                return await self.create_one(upsert_vector, upsert_metadata)

        except Exception as e:
            self.logger.error(f"Failed to upsert point: {e}", exc_info=True)
            raise

    async def update_one(
        self,
        match: dict,
        update_vector: list[float] | None = None,
        update_metadata: dict | None = None,
    ) -> str:
        self.logger.info("Updating one point by match...")
        self.logger.debug(
            f"update vector: {truncate(str(update_vector), QdrantWriter.LOG_MAX_VECTOR_LENGTH) if update_vector else None}, "
            f"update metadata: {truncate(str(update_metadata), QdrantWriter.LOG_MAX_UPDATE_METADATA_LENGTH) if update_metadata else None}, "
            f"match: {truncate(str(match), QdrantWriter.LOG_MAX_MATCH_LENGTH)}"
        )
        try:
            self._validate_update_operation(update_vector, update_metadata, match=match)

            ids = self._find_points_by_match(match)
            if not ids:
                raise ValueError(f"No points found with match: {match}")
            if len(ids) > 1:
                self.logger.warning(f"Found {len(ids)} points for match, using first one")

            point_id = str(ids[0])
            points = self._client.engine.retrieve(
                collection_name=self.collection_name,
                ids=[point_id],
                with_vectors=True,
                with_payload=True,
            )
            if not points:
                raise ValueError(f"Point {point_id} not found")
            old_point = points[0]

            new_vector = update_vector if update_vector is not None else old_point.vector
            new_metadata = update_metadata if update_metadata is not None else old_point.payload

            self._client.engine.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=new_vector,
                        payload=new_metadata,
                    )
                ],
            )
            self.logger.info(f"Updated point {point_id}")
            return point_id

        except Exception as e:
            self.logger.error(f"Failed to update point: {e}", exc_info=True)
            raise

    async def delete_one(self, match: dict) -> str:
        self.logger.info("Deleting one point by match...")
        self.logger.debug(f"match: {truncate(str(match), QdrantWriter.LOG_MAX_MATCH_LENGTH)}")
        try:
            self._validate_delete_operation(match=match)

            ids = self._find_points_by_match(match)
            if not ids:
                raise ValueError(f"No points found with match: {match}")
            if len(ids) > 1:
                self.logger.warning(f"Found {len(ids)} points for match, using first one")

            point_id = str(ids[0])
            self._client.engine.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[point_id]),
            )
            self.logger.info(f"Deleted point {point_id}")
            return point_id

        except Exception as e:
            self.logger.error(f"Failed to delete point: {e}", exc_info=True)
            raise

    async def create_many(self, vectors: list[VectorAdd]) -> list[str]:
        self.logger.info(f"Creating {len(vectors)} points...")
        vector_list = [vec.vector for vec in vectors]
        metadata_list = [vec.metadata for vec in vectors]
        self.logger.debug(
            f"first vector: {truncate(str(vector_list[0]), QdrantWriter.LOG_MAX_VECTOR_LENGTH) if vector_list else None}, "
            f"first metadata: {truncate(str(metadata_list[0]), QdrantWriter.LOG_MAX_CREATE_METADATA_LENGTH) if metadata_list else None}"
        )
        try:
            self._validate_create_operation(vector_list, metadata_list)

            points = []
            ids_result = []
            for item in vectors:
                point_id = str(uuid.uuid4())
                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=item.vector,
                        payload=item.metadata,
                    )
                )
                ids_result.append(point_id)

            for i in range(0, len(points), self.batch_size):
                batch = points[i:i + self.batch_size]
                self._client.engine.upsert(
                    collection_name=self.collection_name,
                    points=batch,
                )

            self.logger.info(f"Created {len(ids_result)} points")
            return ids_result

        except Exception as e:
            self.logger.error(f"Failed to create many points: {e}", exc_info=True)
            raise

    async def upsert_many(self, vectors: list[VectorAdd], conflict_properties: list[str]) -> list[str]:
        self.logger.info(f"Upserting {len(vectors)} points...")
        vector_list = [vec.vector for vec in vectors]
        metadata_list = [vec.metadata for vec in vectors]
        self.logger.debug(
            f"first vector: {truncate(str(vector_list[0]), QdrantWriter.LOG_MAX_VECTOR_LENGTH) if vector_list else None}, "
            f"first metadata: {truncate(str(metadata_list[0]), QdrantWriter.LOG_MAX_CREATE_METADATA_LENGTH) if metadata_list else None}, "
            f"conflict properties: {truncate(str(conflict_properties), QdrantWriter.LOG_MAX_CONFLICT_PROPERTIES_LENGTH)}"
        )
        try:
            self._validate_upsert_operation(vector_list, metadata_list, conflict_properties)

            match_list = []
            for item in vectors:
                match = {prop: item.metadata.get(prop) for prop in conflict_properties}
                match_list.append(match)

            point_ids_dict = {}
            if match_list:
                qfilter = build_should_filter(match_list)
                if qfilter:
                    offset = None
                    while True:
                        points, next_offset = self._client.engine.scroll(
                            collection_name=self.collection_name,
                            scroll_filter=qfilter,
                            limit=self.scroll_limit,
                            offset=offset,
                            with_payload=True,
                            with_vectors=False,
                        )
                        for point in points:
                            for idx, match in enumerate(match_list):
                                if all(point.payload.get(k) == v for k, v in match.items()):
                                    point_ids_dict[idx] = point.id
                                    break

                        if not next_offset:
                            break
                        offset = next_offset

            points_to_upsert = []
            ids_result = []
            for idx, item in enumerate(vectors):
                old_point_id = point_ids_dict.get(idx, None)

                if old_point_id:
                    point_id = old_point_id
                else:
                    point_id = str(uuid.uuid4())

                points_to_upsert.append(
                    models.PointStruct(
                        id=point_id,
                        vector=item.vector,
                        payload=item.metadata,
                    )
                )
                ids_result.append(point_id)

            for i in range(0, len(points_to_upsert), self.batch_size):
                batch = points_to_upsert[i:i + self.batch_size]
                self._client.engine.upsert(
                    collection_name=self.collection_name,
                    points=batch,
                )

            self.logger.info(f"Upserted {len(ids_result)} points")
            return [str(id) for id in ids_result]

        except Exception as e:
            self.logger.error(f"Failed to upsert many points: {e}", exc_info=True)
            raise

    async def update_many(self, updates: list[VectorUpdate]) -> list[str]:
        self.logger.info(f"Updating {len(updates)} points...")
        vector_list = [item.update_vector for item in updates]
        metadata_list = [item.update_metadata for item in updates]
        match_list = [item.match for item in updates]
        self.logger.debug(
            f"first vector: {truncate(str(vector_list[0]), QdrantWriter.LOG_MAX_VECTOR_LENGTH) if vector_list else None}, "
            f"first metadata: {truncate(str(metadata_list[0]), QdrantWriter.LOG_MAX_CREATE_METADATA_LENGTH) if metadata_list else None}, "
            f"first match: {truncate(str(match_list[0]), QdrantWriter.LOG_MAX_MATCH_LENGTH) if match_list else None}"
        )
        try:
            self._validate_update_operation(vector_list, metadata_list, match_list)

            qfilter = build_should_filter(match_list)
            points_dict = {}
            if qfilter:
                offset = None
                while True:
                    points, next_offset = self._client.engine.scroll(
                        collection_name=self.collection_name,
                        scroll_filter=qfilter,
                        limit=self.scroll_limit,
                        offset=offset,
                        with_payload=True,
                        with_vectors=True,
                    )
                    for point in points:
                        for idx, match in enumerate(match_list):
                            if all(point.payload.get(key) == value for key, value in match.items()):
                                points_dict[idx] = point
                                break

                    if not next_offset:
                        break
                    offset = next_offset

            points_to_upsert = []
            ids_result = []
            for idx, item in enumerate(updates):
                old_point = points_dict.get(idx, None)
                if not old_point:
                    self.logger.warning(f"No point found for match: {item.match}")
                    continue

                point_id = old_point.id
                new_vector = item.update_vector if item.update_vector is not None else old_point.vector
                new_metadata = item.update_metadata if item.update_metadata is not None else old_point.payload
                points_to_upsert.append(
                    models.PointStruct(
                        id=point_id,
                        vector=new_vector,
                        payload=new_metadata,
                    )
                )
                ids_result.append(point_id)

            if len(ids_result) != len(match_list):
                raise RuntimeError(
                    f"Expected {len(match_list)} points, got {len(ids_result)}. "
                    f"Update has been canceled"
                )

            for i in range(0, len(points_to_upsert), self.batch_size):
                batch = points_to_upsert[i:i + self.batch_size]
                self._client.engine.upsert(collection_name=self.collection_name, points=batch)

            self.logger.info(f"Updated {len(ids_result)} points")
            return [str(id) for id in ids_result]

        except Exception as e:
            self.logger.error(f"Failed to update many points: {e}", exc_info=True)
            raise

    async def update_many_by_filter(
        self,
        filter: FilterCondition | FilterGroup,
        update_vector: list[float] | None = None,
        update_metadata: dict | None = None,
    ) -> list[str]:
        self.logger.info("Updating points by filter...")
        self.logger.debug(
            f"update vector: {truncate(str(update_vector), QdrantWriter.LOG_MAX_VECTOR_LENGTH)}, "
            f"update metadata: {truncate(str(update_metadata), QdrantWriter.LOG_MAX_CREATE_METADATA_LENGTH)}, "
            f"filter: {truncate(str(filter), QdrantWriter.LOG_MAX_FILTER_LENGTH)}"
        )
        try:
            self._validate_update_operation(update_vector, update_metadata, filter=filter)

            ids_result = self._find_all_points_by_filter(filter)
            if not ids_result:
                raise RuntimeError("No points found matching the filter")

            points_to_upsert = []
            for i in range(0, len(ids_result), self.batch_size):
                batch_ids = ids_result[i:i + self.batch_size]
                points = self._client.engine.retrieve(
                    collection_name=self.collection_name,
                    ids=batch_ids,
                    with_vectors=True,
                    with_payload=True,
                )
                for point in points:
                    vec = update_vector if update_vector is not None else point.vector
                    meta = update_metadata if update_metadata is not None else point.payload
                    points_to_upsert.append(
                        models.PointStruct(
                            id=point.id,
                            vector=vec,
                            payload=meta,
                        )
                    )

            for i in range(0, len(points_to_upsert), self.batch_size):
                batch = points_to_upsert[i:i + self.batch_size]
                self._client.engine.upsert(collection_name=self.collection_name, points=batch)

            self.logger.info(f"Updated {len(ids_result)} points by filter")
            return [str(id) for id in ids_result]

        except Exception as e:
            self.logger.error(f"Failed to update points by filter: {e}", exc_info=True)
            raise

    async def delete_many(self, match_list: list[dict]) -> list[str]:
        self.logger.info(f"Deleting points by {len(match_list)} matches...")
        self.logger.debug(f"first match: {truncate(str(match_list[0]), QdrantWriter.LOG_MAX_MATCH_LENGTH) if match_list else None}")
        try:
            self._validate_delete_operation(match_list)

            qfilter = build_should_filter(match_list)
            ids_result = []
            offset = None
            while True:
                points, next_offset = self._client.engine.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=qfilter,
                    limit=self.scroll_limit,
                    offset=offset,
                    with_payload=False,
                    with_vectors=False,
                )
                ids_result.extend([p.id for p in points])
                if not next_offset:
                    break
                offset = next_offset

            if len(ids_result) != len(match_list):
                raise RuntimeError(
                    f"Expected {len(match_list)} points, got {len(ids_result)}. "
                    f"Deletion has been canceled"
                )

            for i in range(0, len(ids_result), self.batch_size):
                batch = ids_result[i:i + self.batch_size]
                self._client.engine.delete(
                    collection_name=self.collection_name,
                    points_selector=models.PointIdsList(points=batch),
                )

            self.logger.info(f"Deleted {len(ids_result)} points")
            return [str(id) for id in ids_result]

        except Exception as e:
            self.logger.error(f"Failed to delete many points: {e}", exc_info=True)
            raise

    async def delete_many_by_filter(self, filter: FilterCondition | FilterGroup) -> list[str]:
        self.logger.info("Deleting points by filter...")
        self.logger.debug(f"filter: {truncate(str(filter), QdrantWriter.LOG_MAX_FILTER_LENGTH)}")
        try:
            self._validate_delete_operation(filter=filter)

            ids_result = self._find_all_points_by_filter(filter)
            if not ids_result:
                raise RuntimeError("No points found matching the filter")

            for i in range(0, len(ids_result), self.batch_size):
                batch = ids_result[i:i + self.batch_size]
                self._client.engine.delete(
                    collection_name=self.collection_name,
                    points_selector=models.PointIdsList(points=batch),
                )

            self.logger.info(f"Deleted {len(ids_result)} points by filter")
            return [str(id) for id in ids_result]

        except Exception as e:
            self.logger.error(f"Failed to delete points by filter: {e}", exc_info=True)
            raise

    async def connect(self) -> None:
        await self._client.connect()

    async def close(self) -> None:
        await self._client.close()

    async def ping(self) -> bool:
        return await self._client.ping()
