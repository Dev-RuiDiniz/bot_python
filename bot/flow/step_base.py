"""Base class for all automation flow steps."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class StepContext:
    instance_id: str
    adb: Any
    vision: Any
    logger: logging.Logger
    config: dict[str, Any]


class Step(ABC):
    name = "base"

    @abstractmethod
    def run(self, context: StepContext) -> None:
        """Execute this step."""

    def __str__(self) -> str:
        return self.name
