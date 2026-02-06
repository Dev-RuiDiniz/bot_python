from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from bot.core.exceptions import CriticalFail
from bot.flow.step_06_noko_box import Step06NokoBox
from bot.flow.step_base import StepContext


class FakeADBRecorder:
    def __init__(self, fixture_screen: Path) -> None:
        self.calls = []
        self.fixture_screen = fixture_screen

    def tap(self, x: int, y: int) -> None:
        self.calls.append(("tap", x, y))

    def keyevent(self, keycode: int) -> None:
        self.calls.append(("keyevent", keycode))

    def screencap(self, output_path: str) -> Path:
        self.calls.append(("screencap", output_path))
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.fixture_screen.read_bytes())
        return destination


class FakeVisionNoko:
    def __init__(self, empty: bool, home_on_recovery: bool = True) -> None:
        self.empty = empty
        self.home_on_recovery = home_on_recovery

    def wait_and_click(self, capture_fn, adb, template_name: str, **kwargs):
        adb.tap(100, 100)
        capture_fn()
        return {"score": 0.99, "center": (100, 100)}

    def wait_for(self, capture_fn, template_name: str, **kwargs):
        capture_fn()
        return {"score": 0.99, "center": (100, 100)}

    def exists(self, screen_path: str, template_name: str, threshold: float = 0.90) -> bool:
        if template_name == "noko.vazia":
            return self.empty
        if template_name == "home.tela_home":
            return self.home_on_recovery
        return False

    def click_template(self, capture_fn, adb, template_name: str, **kwargs):
        adb.tap(50, 50)
        capture_fn()
        return {"score": 0.95, "center": (50, 50)}


class Step06NokoBoxTests(unittest.TestCase):
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
            logger=logging.getLogger("tests.step06"),
            config={"step_06": {"timeout_enter": 1, "timeout_collect": 1, "collect_clicks": 2}},
        )

    def test_noko_vazia(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionNoko(empty=True)

        context = self._context(adb, vision)
        Step06NokoBox().run(context)

        stats = context.metrics["step_06_noko_box"]
        self.assertEqual(stats["empty"], 1)
        self.assertEqual(stats["collected"], 0)

    def test_noko_nao_vazia_collects(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionNoko(empty=False)

        context = self._context(adb, vision)
        Step06NokoBox().run(context)

        stats = context.metrics["step_06_noko_box"]
        self.assertEqual(stats["empty"], 0)
        self.assertEqual(stats["collected"], 2)

    def test_critical_when_cannot_recover_home(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionNoko(empty=True, home_on_recovery=False)

        with self.assertRaises(CriticalFail):
            Step06NokoBox().run(self._context(adb, vision))


if __name__ == "__main__":
    unittest.main()
