import logging
from logging.handlers import RotatingFileHandler
from src.config.loader import load_logging_config
from paths.project_paths import ProjectPaths


def get_logger(type_name: str):
    paths = ProjectPaths()
    config = load_logging_config(paths.LOGGING_CONFIG).get_type_config(type_name=type_name)

    logger_name = config.name
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    if config.console.use_colors:
        try:
            import colorlog

            color_fmt = f"%(log_color)s{config.fmt}%(reset)s"
            formatter = colorlog.ColoredFormatter(
                fmt=color_fmt,
                datefmt=config.datefmt,
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
            formatter = logging.Formatter(fmt=config.fmt, datefmt=config.datefmt)
    else:
        formatter = logging.Formatter(fmt=config.fmt, datefmt=config.datefmt)

    if config.console.enable:
        console = logging.StreamHandler()
        level = config.console.level
        if not isinstance(level, int):
            level = getattr(logging, level.upper(), logging.INFO)
        console.setLevel(level)
        console.setFormatter(formatter)
        logger.addHandler(console)

    if config.file.enable:
        type_log_dir = paths.LOGS / logger_name
        type_log_dir.mkdir(parents=True, exist_ok=True)

        file = RotatingFileHandler(
            filename=str(
                type_log_dir / config.filename_pattern
            ),
            maxBytes=config.file.max_bytes,
            backupCount=config.file.backup_count,
            encoding=config.encoding,
        )

        level = config.file.level
        if not isinstance(level, int):
            level = getattr(logging, level.upper(), logging.INFO)
        file.setLevel(level)

        file.setFormatter(formatter)
        logger.addHandler(file)

    return logger
