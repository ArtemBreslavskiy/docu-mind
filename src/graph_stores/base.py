from abc import ABC, abstractmethod
from typing import Any


class BaseGraphStore(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @abstractmethod
    def query(self, query: str, parameters: dict[str, Any] = None) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def create_node(self, label: str, properties: dict[str, Any]) -> str:
        ...

    @abstractmethod
    def create_relationship(self, from_node_id: str, to_node_id: str, rel_type: str, properties: dict[str, Any] = None):
        ...

    @abstractmethod
    def get_node(self, node_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def close(self) -> None:
        ...
