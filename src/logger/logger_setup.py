import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Union
import yaml
from src.config.loader import load_logging_config
from paths.project_paths import ProjectPaths

_config = None
_log_dir = None
_initialized = False


def _setup_logger(type_name: str):
    global _config, _log_dir
    if not _initialized:
        raise RuntimeError("Call configure_loggers() first")

    params = {
        **_config["default"],
        **_config["types"].get(type_name, {}),
    }
    logger_name = params.get("name", f"segmentation_bg.{type_name}")
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    if params.get("file", True):
        type_log_dir = _log_dir / logger_name
        type_log_dir.mkdir(parents=True, exist_ok=True)

    fmt = params.get("fmt", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    datefmt = params.get("datefmt", "%Y-%m-%d %H:%M:%S")
    use_colors = params.get("use_colors", False)

    if use_colors:
        try:
            import colorlog

            color_fmt = f"%(log_color)s{fmt}%(reset)s"
            formatter = colorlog.ColoredFormatter(
                fmt=color_fmt,
                datefmt=datefmt,
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
                style="%",
            )
        except ImportError:
            formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    else:
        formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    if params.get("console", True):
        console = logging.StreamHandler()
        level = params.get("console_level", "INFO")
        if not isinstance(level, int):
            level = getattr(logging, level.upper(), logging.INFO)
        console.setLevel(level)
        console.setFormatter(formatter)
        logger.addHandler(console)

    if params.get("file", True):
        file = RotatingFileHandler(
            filename=str(
                type_log_dir / datetime.now().strftime(params["filename_pattern"])
            ),
            maxBytes=params.get("max_bytes", 10_485_760),
            backupCount=params.get("backup_count", 5),
            encoding=params.get("encoding", "utf-8"),
        )

        level = params.get("file_level", "INFO")
        if not isinstance(level, int):
            level = getattr(logging, level.upper(), logging.INFO)
        file.setLevel(level)

        file.setFormatter(formatter)
        logger.addHandler(file)

    return logger


def configure_loggers(
    config_path: Union[str, Path] = None,
    log_dir: Union[str, Path] = None
):
    global _config, _log_dir, _initialized
    if _initialized:
        return

    with open(config_path) as f:
        _config = yaml.safe_load(f)

    _log_dir = Path(log_dir)
    _log_dir.mkdir(parents=True, exist_ok=True)

    _initialized = True


def get_logger(type_name: str):
    if not _initialized:
        paths = ProjectPaths()
        configure_loggers(paths.LOGGING_CONFIG, paths.LOGS)
    return _setup_logger(type_name)


if __name__ == "__main__":
    if not _initialized:
        paths = ProjectPaths()
        configure_loggers(paths.LOGGING_CONFIG, paths.LOGS)
