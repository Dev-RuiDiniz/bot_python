from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from bot.core.exceptions import CriticalFail, SoftFail
from bot.flow.step_01_home import Step01Home
from bot.flow.step_base import StepContext


class FakeVisionForStep01:
    def __init__(self, home_on_attempt: int | None = None, conn_attempts=None, crash_attempts=None) -> None:
        self.home_on_attempt = home_on_attempt
        self.conn_attempts = set(conn_attempts or [])
        self.crash_attempts = set(crash_attempts or [])
        self.current_attempt = 0

    def wait_for(self, capture_fn, template_name: str, timeout_s: int = 0):
        self.current_attempt += 1
        capture_fn()
        if self.home_on_attempt == self.current_attempt:
            return {"score": 0.99, "center": (200, 140)}
        raise SoftFail("home não encontrada")

    def exists(self, screen_path: str, template_name: str, threshold: float = 0.90) -> bool:
        if template_name == "erros.popup_erro_conexao":
            return self.current_attempt in self.conn_attempts
        if template_name == "erros.app_crash":
            return self.current_attempt in self.crash_attempts
        if template_name == "home.tela_home":
            return self.home_on_attempt == self.current_attempt
        return False

    def click_template(self, *args, **kwargs):
        return {"score": 0.95, "center": (10, 10)}


class FakeADBRecorder:
    def __init__(self, fixture_screen: Path) -> None:
        self.calls = []
        self.fixture_screen = fixture_screen

    def start_app(self, package: str, activity: str) -> None:
        self.calls.append(("start_app", package, activity))

    def stop_app(self, package: str) -> None:
        self.calls.append(("stop_app", package))

    def keyevent(self, keycode: int) -> None:
        self.calls.append(("keyevent", keycode))

    def tap(self, x: int, y: int) -> None:
        self.calls.append(("tap", x, y))

    def screencap(self, output_path: str) -> Path:
        self.calls.append(("screencap", output_path))
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.fixture_screen.read_bytes())
        return destination


class Step01HomeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fixture = Path(self.temp_dir.name) / "mock_screen.txt"
        self.fixture.write_text("mock-screen", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _context(self, adb, vision) -> StepContext:
        return StepContext(
            instance_id="inst_test",
            adb=adb,
            vision=vision,
            logger=logging.getLogger("tests.step01"),
            config={
                "app_package": "com.example",
                "app_activity": ".Main",
                "step_01": {"max_attempts": 3, "home_timeout_s": 1, "recovery_back_limit": 2},
            },
        )

    def test_success_home_appears(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionForStep01(home_on_attempt=1)

        Step01Home().run(self._context(adb, vision))
        starts = [c for c in adb.calls if c[0] == "start_app"]
        self.assertEqual(len(starts), 1)

    def test_connection_error_recovers(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionForStep01(home_on_attempt=2, conn_attempts={1})

        Step01Home().run(self._context(adb, vision))
        keyevents = [c for c in adb.calls if c[0] == "keyevent"]
        self.assertGreaterEqual(len(keyevents), 1)

    def test_crash_stops_and_relaunches(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionForStep01(home_on_attempt=2, crash_attempts={1})

        Step01Home().run(self._context(adb, vision))
        stops = [c for c in adb.calls if c[0] == "stop_app"]
        starts = [c for c in adb.calls if c[0] == "start_app"]
        self.assertEqual(len(stops), 1)
        self.assertEqual(len(starts), 2)

    def test_critical_fail_after_max_attempts(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionForStep01(home_on_attempt=None)

        with self.assertRaises(CriticalFail):
            Step01Home().run(self._context(adb, vision))


if __name__ == "__main__":
    unittest.main()
