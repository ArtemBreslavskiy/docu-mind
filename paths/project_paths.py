from pathlib import Path


class ProjectPaths:
    ROOT: Path = Path(__file__).parent.parent

    CONFIGS: Path = ROOT / "configs"
    LOGS: Path = ROOT / "logs"
    DATA: Path = ROOT / "data"

    AGENT_CONFIG: Path = CONFIGS / "agent.yaml"
    APP_CONFIG: Path = CONFIGS / "app.yaml"
    PIPELINE_CONFIG: Path = CONFIGS / "pipeline.yaml"
    LOGGING_CONFIG: Path = CONFIGS / "logging.yaml"

    RAW: Path = DATA / "raw"
    PROCESSED: Path = DATA / "processed"

    CHUNKS: Path = PROCESSED / "chunks.json"
    STORE: Path = PROCESSED / "store"
    TEXTS: Path = PROCESSED / "texts"
