from src.config.schemas.app import LLMConfig
from src.core.generator.base import BaseGenerator
from src.core.generator.ollama_generator import OllamaGenerator


def create_generator(config: LLMConfig):
    if config.provider == "ollama":
        return OllamaGenerator(config)
    else:
        raise ValueError(f"Unknown LLM provider: {config.type}")