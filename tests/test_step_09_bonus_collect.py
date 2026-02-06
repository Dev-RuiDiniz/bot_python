from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from bot.core.exceptions import SoftFail
from bot.flow.step_09_bonus_collect import Step09BonusCollect
from bot.flow.step_base import StepContext


class FakeADBRecorder:
    def __init__(self, fixture_screen: Path) -> None:
        self.calls = []
        self.fixture_screen = fixture_screen

    def start_app(self, package: str, activity: str) -> None:
        self.calls.append(("start_app", package, activity))

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


class FakeVisionBonus:
    def __init__(self, available: bool = False, unavailable: bool = False) -> None:
        self.available = available
        self.unavailable = unavailable

    def wait_and_click(self, capture_fn, adb, template_name: str, **kwargs):
        adb.tap(5, 5)
        capture_fn()
        return {"score": 0.99, "center": (5, 5)}

    def wait_for(self, capture_fn, template_name: str, **kwargs):
        capture_fn()
        return {"score": 0.99, "center": (5, 5)}

    def exists(self, screen_path: str, template_name: str, threshold: float = 0.9) -> bool:
        if template_name == "bonus.botao_bonus_disponivel":
            return self.available
        if template_name == "bonus.bonus_indisponivel":
            return self.unavailable
        if template_name == "home.tela_home":
            return True
        return False


class Step09BonusCollectTests(unittest.TestCase):
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
            logger=logging.getLogger("tests.step09"),
            config={"app_package": "com.game", "app_activity": ".Main", "step_09": {"timeout_bonus": 1}},
        )

    def test_bonus_available_collects(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionBonus(available=True)
        context = self._context(adb, vision)
        Step09BonusCollect().run(context)
        self.assertEqual(context.metrics["step_09_bonus_collect"]["collected"], 1)

    def test_bonus_unavailable_continues(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionBonus(unavailable=True)
        context = self._context(adb, vision)
        Step09BonusCollect().run(context)
        self.assertEqual(context.metrics["step_09_bonus_collect"]["unavailable"], 1)

    def test_bonus_without_indicators_softfail(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionBonus(available=False, unavailable=False)
        with self.assertRaises(SoftFail):
            Step09BonusCollect().run(self._context(adb, vision))


if __name__ == "__main__":
    unittest.main()
