from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from bot.core.exceptions import CriticalFail, SoftFail
from bot.flow.step_04_amigos import Step04Amigos
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


class FakeVisionAmigos:
    def __init__(self, loops, enter_ok=True, home_on_recovery=True):
        self.loops = loops
        self.enter_ok = enter_ok
        self.home_on_recovery = home_on_recovery
        self.loop_idx = 0

    def wait_and_click(self, capture_fn, adb, template_name: str, **kwargs):
        if template_name == "amigos.botao_entrar" and not self.enter_ok:
            raise SoftFail("não entrou")
        if template_name in {"amigos.botao_recolher", "amigos.botao_enviar", "amigos.botao_entrar"}:
            adb.tap(100, 100)
        capture_fn()
        return {"score": 0.99, "center": (100, 100)}


    def click_template(self, capture_fn, adb, template_name: str, **kwargs):
        adb.tap(50, 50)
        capture_fn()
        return {"score": 0.95, "center": (50, 50)}

    def wait_for(self, capture_fn, template_name: str, **kwargs):
        capture_fn()
        if template_name == "amigos.tela_amigos" and not self.enter_ok:
            raise SoftFail("sem tela amigos")
        return {"score": 0.99, "center": (100, 100)}

    def exists(self, screen_path: str, template_name: str, threshold: float = 0.90) -> bool:
        if template_name == "home.tela_home":
            return self.home_on_recovery
        if self.loop_idx >= len(self.loops):
            return template_name == "amigos.sem_presentes"

        state = self.loops[self.loop_idx]
        if template_name == "amigos.botao_recolher" and state == "recolher":
            self.loop_idx += 1
            return True
        if template_name == "amigos.botao_enviar" and state == "enviar":
            self.loop_idx += 1
            return True
        if template_name == "amigos.sem_presentes" and state == "sem":
            return True
        return False


class Step04AmigosTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fixture = Path(self.temp_dir.name) / "mock_screen.txt"
        self.fixture.write_text("mock-screen", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _context(self, adb, vision, max_interactions: int = 6) -> StepContext:
        return StepContext(
            instance_id="inst_test",
            adb=adb,
            vision=vision,
            logger=logging.getLogger("tests.step04"),
            config={
                "step_04": {
                    "cycles": 1,
                    "timeout_enter": 1,
                    "timeout_loop": 1,
                    "max_interactions": max_interactions,
                    "enter_retries": 2,
                    "click_jitter_px": 0,
                }
            },
        )

    def test_presentes_flow_collects_and_sends(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionAmigos(["recolher", "enviar", "sem"])

        context = self._context(adb, vision)
        Step04Amigos().run(context)

        stats = context.metrics["step_04_amigos"]
        self.assertEqual(stats["collected"], 1)
        self.assertEqual(stats["sent"], 1)

    def test_sem_presentes_stops_fast(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionAmigos(["sem"])

        context = self._context(adb, vision)
        Step04Amigos().run(context)

        stats = context.metrics["step_04_amigos"]
        self.assertEqual(stats["interactions"], 0)

    def test_max_interactions_prevents_infinite_loop(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionAmigos(["recolher"] * 50)

        context = self._context(adb, vision, max_interactions=3)
        Step04Amigos().run(context)

        self.assertEqual(context.metrics["step_04_amigos"]["interactions"], 3)

    def test_softfail_when_cannot_enter_amigos(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionAmigos(["sem"], enter_ok=False)

        with self.assertRaises(SoftFail):
            Step04Amigos().run(self._context(adb, vision))

    def test_critical_fail_when_not_back_to_home(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionAmigos(["sem"], home_on_recovery=False)

        with self.assertRaises(CriticalFail):
            Step04Amigos().run(self._context(adb, vision))


if __name__ == "__main__":
    unittest.main()
