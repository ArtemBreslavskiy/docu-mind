from pydantic import BaseModel, Field
from typing import Literal


class BaseClientConfig(BaseModel):
    model_config = {"extra": "forbid"}
    provider: str


class OllamaClientConfig(BaseClientConfig):
    provider: Literal["ollama"]
    model: str
    temperature: float = Field(0.1, ge=0, le=2)
    max_tokens: int = Field(512, gt=0, le=4096)
    base_url: str = "http://localhost:11434"


class OpenAiClientConfig(BaseClientConfig):
    provider: Literal["openai"]
    model: str
    temperature: float = Field(0.1, ge=0, le=2)
    max_tokens: int = Field(512, gt=0, le=4096)


class GoogleClientConfig(BaseClientConfig):
    provider: Literal["google"]
    model: str
    temperature: float = Field(0.1, ge=0, le=2)
    max_output_tokens: int = Field(512, gt=0, le=4096)


class GroqClientConfig(BaseClientConfig):
    provider: Literal["groq"]
    model: str
    temperature: float = Field(0.1, ge=0, le=2)
    max_tokens: int = Field(512, gt=0, le=4096)
