from src.data.loaders.base import BaseLoader
from src.data.loaders.html_loader import HTMLLoader
from src.config.schemas.app import LoaderConfig
from paths.project_paths import ProjectPaths


def create_loader(config: LoaderConfig) -> BaseLoader:
    paths = ProjectPaths()

    if config.type == "html":
        return HTMLLoader(paths.RAW)
    else:
        raise ValueError(f"Unknown loader type: {config.type}")
