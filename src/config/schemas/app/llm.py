from pydantic import BaseModel, Field
from typing import Union
from src.config.schemas.app.prompts import PromptsConfig
from src.config.schemas.app.clients import (
    OllamaClientConfig,
    OpenAiClientConfig,
    GroqClientConfig,
    GoogleClientConfig,
)


class LLMConfig(BaseModel):
    client: Union[
        OllamaClientConfig,
        OpenAiClientConfig,
        GoogleClientConfig,
        GroqClientConfig,
    ] = (Field(discriminator="provider"))
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
