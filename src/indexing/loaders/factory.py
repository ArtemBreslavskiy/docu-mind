from src.logger.logger_setup import get_logger
from indexing.loaders.base import BaseLoader


def create_loader(loader_type: str) -> BaseLoader:
    if loader_type == "html":
        from indexing.loaders.html_loader import HTMLLoader
        logger = get_logger("pipeline")
        return HTMLLoader(logger=logger)
    else:
        raise ValueError(f"Unknown loader type: {loader_type}")
