"""Central configuration and logging setup for the data pipeline."""

import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"

for directory in (RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger that writes to both console and a file.

    Args:
        name: Name of the module requesting the logger, typically __name__.

    Returns:
        A logging.Logger instance with console + file handlers attached
        (attached only once, even if called repeatedly for the same name).
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        file_handler = logging.FileHandler(BASE_DIR / "pipeline.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
