"""Base class for all automation flow steps."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from bot.core.adb_interface import IAdb


@dataclass(slots=True)
class StepContext:
    instance_id: str
    adb: IAdb
    vision: Any
    logger: logging.Logger
    config: dict[str, Any]
    run_id: str = "manual"
    metrics: dict[str, Any] = field(default_factory=dict)


class Step(ABC):
    name = "base"

    @abstractmethod
    def run(self, context: StepContext) -> None:
        """Execute this step."""

    def __str__(self) -> str:
        return self.name
