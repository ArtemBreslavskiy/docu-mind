import os
from langchain_core.language_models.chat_models import BaseChatModel
from config.schemas.app.clients import BaseClientConfig


def create_llm(config: BaseClientConfig) -> BaseChatModel:
    if config.provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            base_url=config.base_url,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

    elif config.provider == "openai":
        from langchain_openai import ChatOpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided (set OPENAI_API_KEY in env)")

        return ChatOpenAI(
            api_key=api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

    elif config.provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key not provided (set GOOGLE_API_KEY in env)")

        return ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=config.model,
            temperature=config.temperature,
            max_output_tokens=config.max_output_tokens,
        )

    elif config.provider == "groq":
        from langchain_openai import ChatOpenAI

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Groq API key not provided (set GROQ_API_KEY in env)")

        return ChatOpenAI(
            api_key=api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    else:
        raise ValueError(f"Unsupported LLM client provider: {config.provider}")
