from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from bot.core.exceptions import CriticalFail, SoftFail
from bot.flow.step_05_roleta_principal import Step05RoletaPrincipal
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


class FakeVisionRoleta:
    def __init__(self, fail_on_spin: int | None = None, home_on_recovery: bool = True) -> None:
        self.fail_on_spin = fail_on_spin
        self.home_on_recovery = home_on_recovery
        self.spin_clicks = 0

    def wait_and_click(self, capture_fn, adb, template_name: str, **kwargs):
        if template_name == "roleta.botao_girar":
            self.spin_clicks += 1
        adb.tap(100, 100)
        capture_fn()
        return {"score": 0.99, "center": (100, 100)}

    def wait_for(self, capture_fn, template_name: str, **kwargs):
        capture_fn()
        if template_name == "roleta.resultado" and self.fail_on_spin == self.spin_clicks:
            raise SoftFail("timeout aguardando resultado")
        return {"score": 0.99, "center": (100, 100)}

    def exists(self, screen_path: str, template_name: str, threshold: float = 0.90) -> bool:
        if template_name == "home.tela_home":
            return self.home_on_recovery
        return False

    def click_template(self, capture_fn, adb, template_name: str, **kwargs):
        adb.tap(50, 50)
        capture_fn()
        return {"score": 0.95, "center": (50, 50)}


class Step05RoletaPrincipalTests(unittest.TestCase):
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
            logger=logging.getLogger("tests.step05"),
            config={"step_05": {"spins": 2, "spin_timeout": 1, "result_timeout": 1}},
        )

    def test_success_two_spins(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionRoleta()

        context = self._context(adb, vision)
        Step05RoletaPrincipal().run(context)

        stats = context.metrics["step_05_roleta_principal"]
        self.assertEqual(stats["spins_done"], 2)
        self.assertEqual(stats["timeouts"], 0)

    def test_softfail_when_result_timeout(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionRoleta(fail_on_spin=1)

        with self.assertRaises(SoftFail):
            Step05RoletaPrincipal().run(self._context(adb, vision))

    def test_critical_fail_when_recovery_breaks(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionRoleta(fail_on_spin=1, home_on_recovery=False)

        with self.assertRaises(CriticalFail):
            Step05RoletaPrincipal().run(self._context(adb, vision))


if __name__ == "__main__":
    unittest.main()
