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
    memuc_path: str | None = None

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

    def _execute_memuc(self, args: list[str], timeout: int = 30) -> str | None:
        if not self.memuc_path:
            return None
        command = [self.memuc_path, *args]
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore",
                shell=False,
            )
            stdout, stderr = process.communicate(timeout=timeout)
            if process.returncode == 0:
                return stdout.strip()
            return (stderr or stdout).strip() or None
        except FileNotFoundError:
            return None
        except subprocess.TimeoutExpired:
            process.kill()
            return None
        except Exception:
            return None

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

    def get_screen_resolution(self) -> tuple[int, int]:
        if self.memuc_path:
            output = self._execute_memuc(["adb", "-i", self.serial, "shell", "wm", "size"])
            if output:
                parsed = _parse_wm_size(output)
                if parsed:
                    return parsed
        try:
            output = self._run_text("shell", "wm", "size").stdout
            parsed = _parse_wm_size(output)
            if parsed:
                return parsed
        except CriticalFail:
            pass
        return (1280, 720)

    def is_running(self) -> bool:
        if not self.memuc_path:
            return True
        output = self._execute_memuc(["isrunning", "-i", self.serial])
        return bool(output and "running" in output.lower())

    def launch_instance(self, timeout: int = 120) -> bool:
        if not self.memuc_path:
            self.connect()
            return True
        if self.is_running():
            return True
        self._execute_memuc(["start", "-i", self.serial], timeout=30)
        try:
            self._run_text("wait-for-device", timeout=timeout)
            return True
        except CriticalFail:
            return False

    def list_instances(self) -> list[dict[str, object]]:
        if not self.memuc_path:
            return []
        self._execute_memuc(["none"], timeout=5)
        raw_data = self._execute_memuc(["listv2"], timeout=15)
        if not raw_data or len(raw_data.strip()) < 5:
            raw_data = self._execute_memuc(["list", "-l"], timeout=15)
        if not raw_data:
            return []

        instances: list[dict[str, object]] = []
        for line in raw_data.splitlines():
            parts = line.replace("\t", ",").split(",")
            if len(parts) >= 4 and parts[0].isdigit():
                instances.append(
                    {
                        "index": int(parts[0]),
                        "title": parts[1],
                        "is_running": parts[3] != "-1",
                        "pid": parts[4] if len(parts) > 4 else None,
                    }
                )
        return instances


def _parse_wm_size(output: str) -> tuple[int, int] | None:
    try:
        lines = [line for line in output.splitlines() if "size:" in line.lower()]
        if not lines:
            return None
        value = lines[0].split(":", 1)[1].strip()
        width, height = value.lower().split("x", 1)
        return int(width), int(height)
    except Exception:
        return None
