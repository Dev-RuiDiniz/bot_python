from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from bot.core.exceptions import CriticalFail, Reason, SoftFail
from bot.flow.step_08_chrome_bonus import Step08ChromeBonus
from bot.flow.step_base import StepContext


class FakeADBRecorder:
    def __init__(self, fixture_screen: Path) -> None:
        self.calls = []
        self.fixture_screen = fixture_screen

    def start_app(self, package: str, activity: str) -> None:
        self.calls.append(("start_app", package, activity))

    def open_url(self, url: str) -> None:
        self.calls.append(("open_url", url))

    def input_text(self, text: str) -> None:
        self.calls.append(("input_text", text))

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


class FakeVisionChrome:
    def __init__(self, page_ok: bool = True, captcha: bool = False) -> None:
        self.page_ok = page_ok
        self.captcha = captcha

    def wait_and_click(self, capture_fn, adb, template_name: str, **kwargs):
        adb.tap(1, 1)
        capture_fn()
        return {"score": 0.99, "center": (1, 1)}

    def wait_for(self, capture_fn, template_name: str, **kwargs):
        capture_fn()
        if template_name == "chrome.pagina_bonus" and not self.page_ok:
            raise SoftFail("timeout")
        return {"score": 0.99, "center": (1, 1)}

    def exists(self, screen_path: str, template_name: str, threshold: float = 0.9) -> bool:
        if template_name == "chrome.captcha":
            return self.captcha
        return False


class Step08ChromeBonusTests(unittest.TestCase):
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
            logger=logging.getLogger("tests.step08"),
            config={
                "chrome_package": "com.android.chrome",
                "chrome_activity": "com.google.android.apps.chrome.Main",
                "step_08": {"timeout_page": 1, "navigation_mode": "intent", "bonus_url": "https://bonus"},
            },
        )

    def test_chrome_ok(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionChrome(page_ok=True)
        Step08ChromeBonus().run(self._context(adb, vision))
        self.assertIn(("open_url", "https://bonus"), adb.calls)

    def test_captcha_detected_critical(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionChrome(page_ok=False, captcha=True)
        with self.assertRaises(CriticalFail) as err:
            Step08ChromeBonus().run(self._context(adb, vision))
        self.assertEqual(err.exception.reason, Reason.CAPTCHA_DETECTED)

    def test_bonus_page_not_found_reason(self) -> None:
        adb = FakeADBRecorder(self.fixture)
        vision = FakeVisionChrome(page_ok=False, captcha=False)
        with self.assertRaises(CriticalFail) as err:
            Step08ChromeBonus().run(self._context(adb, vision))
        self.assertEqual(err.exception.reason, Reason.BONUS_PAGE_NOT_FOUND)

if __name__ == "__main__":
    unittest.main()
