"""Fake ADB implementation for deterministic no-device tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class FakeADB:
    serial: str = "fake-serial"
    screens: list[Path] = field(default_factory=list)
    current_screen: int = 0
    actions: list[tuple[str, tuple[object, ...]]] = field(default_factory=list)
    calls: list[tuple[str, tuple[object, ...]]] = field(default_factory=list)

    def __init__(self, screens: Iterable[str | Path] | None = None, serial: str = "fake-serial") -> None:
        self.serial = serial
        self.screens = [Path(s) for s in (screens or [])]
        self.current_screen = 0
        self.actions = []
        self.calls = self.actions

    def set_screens(self, screens: Iterable[str | Path]) -> None:
        self.screens = [Path(s) for s in screens]
        self.current_screen = 0

    def advance_screen(self) -> None:
        if self.current_screen < len(self.screens) - 1:
            self.current_screen += 1

    def connect(self) -> None:
        self.calls.append(("connect", ()))

    def tap(self, x: int, y: int) -> None:
        self.calls.append(("tap", (x, y)))

    def keyevent(self, keycode: int) -> None:
        self.calls.append(("keyevent", (keycode,)))

    def start_app(self, package: str, activity: str) -> None:
        self.calls.append(("start_app", (package, activity)))

    def launch_app(self, package: str, activity: str) -> None:
        self.start_app(package, activity)

    def get_screen_resolution(self) -> tuple[int, int]:
        return (1280, 720)

    def is_running(self) -> bool:
        return True

    def launch_instance(self, timeout: int = 120) -> bool:
        self.calls.append(("launch_instance", (timeout,)))
        return True

    def list_instances(self) -> list[dict[str, object]]:
        return []

    def stop_app(self, package: str) -> None:
        self.calls.append(("stop_app", (package,)))

    def input_text(self, text: str) -> None:
        self.calls.append(("input_text", (text,)))

    def open_url(self, url: str) -> None:
        self.calls.append(("open_url", (url,)))

    def screencap(self, output_path: str) -> Path:
        self.calls.append(("screencap", (output_path,)))
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        if not self.screens:
            destination.write_bytes(b"")
            return destination

        source = self.screens[min(self.current_screen, len(self.screens) - 1)]
        destination.write_bytes(source.read_bytes())
        self.advance_screen()
        return destination
