"""Per-instance logger helpers."""

from __future__ import annotations

import logging
from pathlib import Path


def setup_instance_logger(instance_id: str, logs_dir: str = "logs") -> logging.Logger:
    """Create a logger that writes both to stdout and an instance file."""
    Path(logs_dir).mkdir(parents=True, exist_ok=True)

    logger_name = f"bot.instance.{instance_id}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(Path(logs_dir) / f"{instance_id}.log")
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger
