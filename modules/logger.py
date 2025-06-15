import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger.json import JsonFormatter
from modules.config import LoggingConfig

def get_logger(config: LoggingConfig) -> logging.Logger:
    logger = logging.getLogger("PowerSnitch")
    logger.setLevel(config.level)

    handler = RotatingFileHandler(
        config.path,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=2
    )

    if config.json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger
