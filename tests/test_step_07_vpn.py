from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from bot.core.exceptions import CriticalFail, SoftFail
from bot.flow.step_07_vpn import Step07VPN
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


class FakeVisionVPN:
    def __init__(self, connected: bool = False, connect_after_click: bool = False, error: bool = False) -> None:
        self.connected = connected
        self.connect_after_click = connect_after_click
        self.error = error

    def wait_and_click(self, capture_fn, adb, template_name: str, **kwargs):
        adb.tap(10, 10)
        capture_fn()
        if template_name == "vpn.conectar" and self.connect_after_click:
            self.connected = True
        return {"score": 0.99, "center": (10, 10)}

    def wait_for(self, capture_fn, template_name: str, **kwargs):
        capture_fn()
        if template_name == "vpn.conectada" and not self.connected:
            raise SoftFail("timeout")
        return {"score": 0.99, "center": (10, 10)}

    def exists(self, screen_path: str, template_name: str, threshold: float = 0.9) -> bool:
        if template_name == "vpn.conectada":
            return self.connected
        if template_name == "vpn.desconectada":
            return not self.connected
        if template_name == "vpn.erro":
            return self.error
        return False


class Step07VPNTests(unittest.TestCase):
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
            logger=logging.getLogger("tests.step07"),
            config={"step_07": {"timeout_connect": 1}},
        )

    def test_vpn_already_connected(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionVPN(connected=True)
        context = self._context(adb, vision)
        Step07VPN().run(context)
        self.assertEqual(context.metrics["step_07_vpn"]["already_connected"], 1)

    def test_vpn_connects_after_click(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionVPN(connected=False, connect_after_click=True)
        context = self._context(adb, vision)
        Step07VPN().run(context)
        self.assertEqual(context.metrics["step_07_vpn"]["connect_clicks"], 1)

    def test_vpn_timeout_critical(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionVPN(connected=False, connect_after_click=False)
        with self.assertRaises(CriticalFail):
            Step07VPN().run(self._context(adb, vision))


if __name__ == "__main__":
    unittest.main()
