"""Multiprocess orchestration for parallel instances."""

from __future__ import annotations

from multiprocessing import Pool
from typing import Any

from bot.config.loader import InstanceConfig
from bot.runner.instance_runner import run_instance


def _run(payload: tuple[InstanceConfig, dict[str, Any]]) -> int:
    return run_instance(*payload)


def run_parallel(instances: list[InstanceConfig], bot_config: dict[str, Any], workers: int | None = None) -> list[int]:
    jobs = [(instance, bot_config) for instance in instances]
    with Pool(processes=workers or len(instances) or 1) as pool:
        return pool.map(_run, jobs)
