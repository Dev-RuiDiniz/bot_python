"""Per-instance logger helpers."""

from __future__ import annotations

import logging
from pathlib import Path


class _RunIdFilter(logging.Filter):
    def __init__(self, run_id: str) -> None:
        super().__init__()
        self.run_id = run_id

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "run_id"):
            record.run_id = self.run_id
        return True


def setup_instance_logger(instance_id: str, run_id: str, logs_dir: str = "logs") -> logging.Logger:
    """Create a logger that writes both to stdout and an instance file."""
    Path(logs_dir).mkdir(parents=True, exist_ok=True)

    logger_name = f"bot.instance.{instance_id}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | [run=%(run_id)s] | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    run_filter = _RunIdFilter(run_id)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(run_filter)

    file_handler = logging.FileHandler(Path(logs_dir) / f"{instance_id}.log")
    file_handler.setFormatter(formatter)
    file_handler.addFilter(run_filter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger
