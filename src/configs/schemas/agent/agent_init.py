from pydantic import BaseModel, Field
from typing import Literal


class BaseAgentInitConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class CustomAgentInitConfig(BaseAgentInitConfig):
    type: Literal["custom"]
    json_parsing: bool = False
    max_iterations: int = Field(5, ge=1, le=20)
