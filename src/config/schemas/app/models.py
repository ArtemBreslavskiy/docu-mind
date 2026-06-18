from pydantic import BaseModel, Field
from typing import Union
from src.config.schemas.app.embedder import SentenceTransformerEmbedderConfig
from src.config.schemas.app.llm import LLMConfig


class ModelsConfig(BaseModel):
    embedder: Union[SentenceTransformerEmbedderConfig] = Field(discriminator="type")
    llm: LLMConfig = Field(default_factory=LLMConfig)
