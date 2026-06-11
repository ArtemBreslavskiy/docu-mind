from src.data.loaders.base import BaseLoader
from src.data.loaders.html_loader import HTMLLoader
from src.config.schemas.app import LoaderConfig


def create_loader(config: LoaderConfig) -> BaseLoader:
    if config.type == "html":
        return HTMLLoader()
    else:
        raise ValueError(f"Unknown loader type: {config.type}")
