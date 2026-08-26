from typing import Any
from src.data.db_prividers.base import BaseDBProvider
from src.data.db.sql.reader.base import BaseSQLReader
from src.data.db.nosql.reader.base import BaseNoSQLReader


class UnifiedDBProvider(BaseDBProvider):
    def __init__(self, readers: list[BaseSQLReader | BaseNoSQLReader], **kwargs):
        super.__init__(**kwargs)
        self.readers = [{"type": reader.type, "name": reader.name, "reader": reader} for reader in readers]

    def get_description(self) -> list[str]: