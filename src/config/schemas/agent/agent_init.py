from pydantic import BaseModel, Field
from typing import Literal
from abc import ABC, abstractmethod


class BaseAgentInitConfig(BaseModel, ABC):
    model_config = {"extra": "forbid"}

    @property
    @abstractmethod
    def type(self) -> str:
        ...


class CustomAgentInitConfig(BaseAgentInitConfig):
    type: Literal["custom"]
    json_parsing: bool = False
    max_iterations: int = Field(5, ge=1, le=20)
