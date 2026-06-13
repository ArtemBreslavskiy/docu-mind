from src.config.schemas.app import ModelConfig
from src.core.models.base import BaseLLMModel
from src.core.models.ollama_model import OllamaModel


def create_model(config: ModelConfig) -> BaseLLMModel:
    if config.provider == "ollama":
        return OllamaModel(config=config)
    else:
        raise ValueError(f"Unknown LLM provider: {config.type}")