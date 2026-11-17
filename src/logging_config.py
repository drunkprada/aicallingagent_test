import logging
from logging.handlers import RotatingFileHandler

from src.config import LOGS_DIR


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("resume_agent")
    if logger.handlers:
        return logger

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    file_handler = RotatingFileHandler(
        LOGS_DIR / "app.log", maxBytes=5_000_000, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
