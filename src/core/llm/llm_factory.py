import os
from langchain_core.language_models.chat_models import BaseChatModel
from src.config.schemas.app import ModelsConfig
from src.config.schemas.clients import (
    OllamaClientConfig,
    OpenAiClientConfig,
    GroqClientConfig,
    GoogleClientConfig,
)


def create_llm(config: ModelsConfig) -> BaseChatModel:
    client_config = config.llm.client

    if isinstance(client_config, OllamaClientConfig):
        from langchain_ollama import ChatOllama

        return ChatOllama(
            base_url=client_config.base_url,
            model=client_config.model,
            temperature=client_config.temperature,
            max_tokens=client_config.max_tokens,
        )

    elif isinstance(client_config, OpenAiClientConfig):
        from langchain_openai import ChatOpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided (set OPENAI_API_KEY in env)")

        return ChatOpenAI(
            api_key=api_key,
            model=client_config.model,
            temperature=client_config.temperature,
            max_tokens=client_config.max_tokens,
        )

    elif isinstance(client_config, GoogleClientConfig):
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key not provided (set GOOGLE_API_KEY in env)")

        return ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=client_config.model,
            temperature=client_config.temperature,
            max_output_tokens=client_config.max_output_tokens,
        )

    elif isinstance(client_config, GroqClientConfig):
        from langchain_openai import ChatOpenAI

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Groq API key not provided (set GROQ_API_KEY in env)")

        return ChatOpenAI(
            api_key=api_key,
            model=client_config.model,
            temperature=client_config.temperature,
            max_tokens=client_config.max_tokens,
        )
    else:
        raise ValueError(f"Unsupported LLM client provider: {client_config.provider}")
