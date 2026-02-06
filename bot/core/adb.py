"""Simple ADB wrapper for command execution and common gestures."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from bot.core.exceptions import CriticalFail
from bot.core.adb_interface import IAdb


@dataclass(slots=True)
class ADBClient(IAdb):
    """ADB wrapper bound to a single device serial."""

    serial: str
    adb_bin: str = "adb"

    def _run_text(self, *args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
        cmd = [self.adb_bin, "-s", self.serial, *args]
        try:
            return subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                check=True,
                timeout=timeout,
            )
        except subprocess.CalledProcessError as exc:
            raise CriticalFail(f"ADB command failed: {' '.join(cmd)}\n{exc.stderr}") from exc
        except subprocess.TimeoutExpired as exc:
            raise CriticalFail(f"ADB command timeout: {' '.join(cmd)}") from exc

    def _run_bytes(self, *args: str, timeout: int = 30) -> subprocess.CompletedProcess[bytes]:
        cmd = [self.adb_bin, "-s", self.serial, *args]
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                check=True,
                timeout=timeout,
            )
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode(errors="replace") if exc.stderr else ""
            raise CriticalFail(f"ADB command failed: {' '.join(cmd)}\n{stderr}") from exc
        except subprocess.TimeoutExpired as exc:
            raise CriticalFail(f"ADB command timeout: {' '.join(cmd)}") from exc

    def connect(self) -> None:
        self._run_text("wait-for-device")

    def tap(self, x: int, y: int) -> None:
        self._run_text("shell", "input", "tap", str(x), str(y))

    def keyevent(self, keycode: int) -> None:
        self._run_text("shell", "input", "keyevent", str(keycode))

    def start_app(self, package: str, activity: str) -> None:
        self._run_text("shell", "am", "start", "-n", f"{package}/{activity}")

    def launch_app(self, package: str, activity: str) -> None:
        """Backward-compatible alias for start_app."""
        self.start_app(package, activity)

    def stop_app(self, package: str) -> None:
        self._run_text("shell", "am", "force-stop", package)

    def input_text(self, text: str) -> None:
        encoded = text.replace(" ", "%s")
        self._run_text("shell", "input", "text", encoded)

    def open_url(self, url: str) -> None:
        self._run_text("shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url)

    def screencap(self, output_path: str) -> Path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        raw = self._run_bytes("exec-out", "screencap", "-p", timeout=60)
        destination.write_bytes(raw.stdout)
        return destination
