from pydantic import BaseModel, Field
from src.config.schemas.app.llm import LLMConfig


class ModelsConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
