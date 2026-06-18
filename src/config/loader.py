import yaml
from pathlib import Path
from config.schemas.agent.agent import AgentConfig
from config.schemas.app.app import AppConfig
from config.schemas.logging.logging import LoggingConfig
from config.schemas.pipeline.pipeline import PipelineConfig


def load_agent_config(path: str | Path) -> AgentConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return AgentConfig(**raw)


def load_app_config(path: str | Path) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return AppConfig(**raw)


def load_logging_config(path: str | Path) -> LoggingConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return LoggingConfig(**raw)


def load_pipeline_config(path: str | Path) -> PipelineConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return PipelineConfig(**raw)
