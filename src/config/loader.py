import yaml
from pathlib import Path
from src.config.schemas.agent import AgentConfig
from src.config.schemas.app import AppConfig
from src.config.schemas.logging import LoggingConfig
from src.config.schemas.pipeline import PipelineConfig


def load_agent_config(path: str | Path) -> AgentConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return AgentConfig(**raw)


def load_app_config(path: str | Path) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return AppConfig(**raw)


def load_logger_config(path: str | Path) -> LoggingConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return LoggingConfig(**raw)


def load_pipeline_config(path: str | Path) -> PipelineConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return PipelineConfig(**raw)
