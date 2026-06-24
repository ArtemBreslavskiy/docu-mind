from pydantic import BaseModel, Field
from typing import Literal


class BaseEmbedderConfig(BaseModel):
    model_config = {"extra": "forbid"}
    type: str


class DisabledEmbedderConfig(BaseEmbedderConfig):
    type: Literal["disabled"]


class SentenceTransformerEmbedderConfig(BaseEmbedderConfig):
    type: Literal["sentence_transformer"]
    name: str = "BAAI/bge-m3"
    device: str = Field("cuda", pattern=r"^(cpu|cuda(:\d+)?)$")
