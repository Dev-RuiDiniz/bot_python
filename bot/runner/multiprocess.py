"""Multiprocess orchestration for parallel instances."""

from __future__ import annotations

from multiprocessing import Process, Queue
from typing import Any

from bot.config.loader import InstanceConfig
from bot.runner.instance_runner import run_instance


def _run(index: int, instance: InstanceConfig, bot_config: dict[str, Any], queue: Queue) -> None:
    code = run_instance(instance, bot_config)
    queue.put((index, code))


def run_parallel(instances: list[InstanceConfig], bot_config: dict[str, Any], workers: int | None = None) -> list[int]:
    _ = workers
    if not instances:
        return []

    queue: Queue = Queue()
    processes: list[Process] = []
    for index, instance in enumerate(instances):
        process = Process(target=_run, args=(index, instance, bot_config, queue), daemon=False)
        processes.append(process)
        process.start()

    results: list[int | None] = [None] * len(instances)
    expected = len(instances)
    received = 0
    while received < expected:
        idx, code = queue.get()
        results[idx] = code
        received += 1

    for index, process in enumerate(processes):
        process.join()
        if results[index] is None:
            # fallback usando exit code do processo quando run_instance não retornou
            results[index] = process.exitcode if process.exitcode is not None else 3

    return [int(code) for code in results]
