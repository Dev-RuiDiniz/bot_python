from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from bot.core.fake_adb import FakeADB
from bot.core.vision import Vision, cv2
from tests.support.mock_images import create_mock_fixture_tree


@unittest.skipIf(cv2 is None, "opencv-python não disponível no ambiente")
class VisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fixtures = Path(self.temp_dir.name)
        self.screens, self.templates = create_mock_fixture_tree(self.fixtures)
        self.vision = Vision(str(self.templates))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_exists(self) -> None:
        screen = self.screens / "screen_with_home.png"
        self.assertTrue(self.vision.exists(str(screen), "home.tela_home", threshold=0.88))
        self.assertFalse(self.vision.exists(str(screen), "erros.app_crash", threshold=0.88))

    def test_wait_for_respects_timeout_and_poll(self) -> None:
        seq = [
            self.screens / "screen_blank.png",
            self.screens / "screen_blank.png",
            self.screens / "screen_with_home.png",
        ]
        adb = FakeADB(seq)

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "screen.png"

            def capture() -> str:
                return str(adb.screencap(str(p)))

            result = self.vision.wait_for(
                capture,
                template_name="home.tela_home",
                timeout_s=2,
                interval_s=0.01,
                threshold=0.88,
            )

        self.assertGreater(result["score"], 0.88)
        screencaps = [call for call in adb.calls if call[0] == "screencap"]
        self.assertGreaterEqual(len(screencaps), 3)

    def test_click_template_clicks_center_and_logs(self) -> None:
        seq = [self.screens / "screen_home_and_button.png"]
        adb = FakeADB(seq)
        logger = logging.getLogger("test.vision.click")

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "screen.png"

            def capture() -> str:
                return str(adb.screencap(str(p)))

            result = self.vision.click_template(
                capture,
                adb,
                "home.botao_home",
                threshold=0.88,
                logger=logger,
            )

        tap_calls = [call for call in adb.calls if call[0] == "tap"]
        self.assertEqual(len(tap_calls), 1)
        self.assertEqual(tap_calls[0][1], result["center"])


    def test_wait_and_click_with_jitter(self) -> None:
        seq = [self.screens / "screen_home_and_button.png"]
        adb = FakeADB(seq)

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "screen.png"

            def capture() -> str:
                return str(adb.screencap(str(p)))

            self.vision.wait_and_click(
                capture,
                adb,
                "home.botao_home",
                timeout_s=1,
                threshold=0.88,
                jitter_px=2,
                post_sleep_s=0,
            )

        tap_calls = [call for call in adb.calls if call[0] == "tap"]
        self.assertEqual(len(tap_calls), 1)

    def test_find_best_returns_score_and_box(self) -> None:
        screen = self.screens / "screen_with_home.png"
        result = self.vision.find_best(str(screen), "home.tela_home")
        self.assertIn("score", result)
        self.assertIn("top_left", result)
        self.assertIn("bottom_right", result)

    def test_template_confidence_override(self) -> None:
        strict = Vision(
            str(self.templates),
            default_confidence=1.01,
            templates_confidence={"home.tela_home": 0.88},
        )
        screen = self.screens / "screen_with_home.png"
        self.assertTrue(strict.exists(str(screen), "home.tela_home"))
        self.assertFalse(strict.exists(str(screen), "home.botao_home"))

if __name__ == "__main__":
    unittest.main()
