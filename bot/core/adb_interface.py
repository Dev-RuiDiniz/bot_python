"""ADB interface contract used by runner and flow steps."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class IAdb(Protocol):
    serial: str

    def connect(self) -> None: ...

    def tap(self, x: int, y: int) -> None: ...

    def keyevent(self, keycode: int) -> None: ...

    def start_app(self, package: str, activity: str) -> None: ...

    def stop_app(self, package: str) -> None: ...

    def screencap(self, output_path: str) -> Path: ...
