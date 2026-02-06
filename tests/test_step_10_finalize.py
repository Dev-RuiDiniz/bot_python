from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from bot.flow.step_10_finalize import Step10Finalize
from bot.flow.step_base import StepContext


class FakeADBRecorder:
    def __init__(self, fixture_screen: Path) -> None:
        self.calls = []
        self.fixture_screen = fixture_screen

    def stop_app(self, package: str) -> None:
        self.calls.append(("stop_app", package))

    def keyevent(self, keycode: int) -> None:
        self.calls.append(("keyevent", keycode))

    def screencap(self, output_path: str) -> Path:
        self.calls.append(("screencap", output_path))
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.fixture_screen.read_bytes())
        return destination


class FakeVisionFinalize:
    def exists(self, screen_path: str, template_name: str, threshold: float = 0.9) -> bool:
        return template_name == "home.tela_home"


class Step10FinalizeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fixture = Path(self.temp_dir.name) / "mock_screen.txt"
        self.fixture.write_text("mock-screen", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_finalize_stops_app_and_marks_finished(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        context = StepContext(
            instance_id="inst_test",
            adb=adb,
            vision=FakeVisionFinalize(),
            logger=logging.getLogger("tests.step10"),
            config={"app_package": "com.game"},
        )

        Step10Finalize().run(context)

        self.assertIn(("stop_app", "com.game"), adb.calls)
        self.assertTrue(context.metrics["finished"])


if __name__ == "__main__":
    unittest.main()
