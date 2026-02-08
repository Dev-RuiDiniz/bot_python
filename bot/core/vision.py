"""OpenCV helpers for template matching and state waiting."""

from __future__ import annotations

import time
import random
import os
from pathlib import Path
from typing import Callable, Optional
import logging

from bot.core.exceptions import SoftFail

cv2 = None

def _lazy_import_cv2():
    global cv2
    if cv2 is None:
        import cv2 as _cv2
        cv2 = _cv2


class Vision:
    def __init__(
        self,
        templates_dir: str,
        template_map: Optional[dict[str, str]] = None,
        default_confidence: float = 0.90,
        templates_confidence: Optional[dict[str, float]] = None,
    ) -> None:
        self.templates_dir = Path(templates_dir)
        self.template_map = template_map or {}
        self.default_confidence = float(default_confidence)
        self.templates_confidence = templates_confidence or {}
        self._templates: dict[str, object] = {}

    def _ensure_cv2(self) -> None:
        try:
            _lazy_import_cv2()
        except Exception:
            raise SoftFail("opencv-python is not available in this environment")

    def _resolve_template_path(self, name: str) -> Path:
        if name in self.template_map:
            return self.templates_dir / self.template_map[name]

        explicit = self.templates_dir / name
        if explicit.exists():
            return explicit

        logical = self.templates_dir / f"{name.replace('.', '/')}.png"
        return logical

    def load_template(self, name: str):
        self._ensure_cv2()
        if name in self._templates:
            return self._templates[name]

        path = self._resolve_template_path(name)
        if not path.exists():
            raise SoftFail(f"Template not found: {path}")
        template = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if template is None:
            raise SoftFail(f"Unable to read template: {path}")
        self._templates[name] = template
        return template

    def _resolve_threshold(self, template_name: str, threshold: Optional[float]) -> float:
        if threshold is not None:
            return float(threshold)
        if template_name in self.templates_confidence:
            return float(self.templates_confidence[template_name])
        return self.default_confidence

    def _save_debug_bbox(self, screen_path: str, best_match: dict[str, object], template_name: str) -> None:
        if os.getenv("DEBUG_VISION") != "1" or cv2 is None:
            return
        screen = cv2.imread(screen_path, cv2.IMREAD_COLOR)
        if screen is None:
            return
        p1 = best_match["top_left"]
        p2 = best_match["bottom_right"]
        cv2.rectangle(screen, p1, p2, (0, 255, 0), 2)
        cv2.putText(
            screen,
            f"{template_name} {best_match['score']:.3f}",
            (p1[0], max(12, p1[1] - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )
        debug_dir = Path("runtime") / "vision_debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_path = debug_dir / f"{Path(screen_path).stem}_{template_name.replace('.', '_')}.png"
        cv2.imwrite(str(debug_path), screen)

    def exists(self, screen_path: str, template_name: str, threshold: Optional[float] = None) -> bool:
        try:
            self.match_template(screen_path, template_name, threshold=threshold)
            return True
        except SoftFail:
            return False

    def find_best(self, screen_path: str, template_name: str) -> dict[str, object]:
        self._ensure_cv2()
        screen = cv2.imread(screen_path, cv2.IMREAD_COLOR)
        if screen is None:
            raise SoftFail(f"Unable to read screenshot: {screen_path}")

        template = self.load_template(template_name)
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        h, w = template.shape[:2]
        best = {
            "score": float(max_val),
            "center": (max_loc[0] + w // 2, max_loc[1] + h // 2),
            "top_left": max_loc,
            "bottom_right": (max_loc[0] + w, max_loc[1] + h),
        }
        self._save_debug_bbox(screen_path, best, template_name)
        return best

    def match_template(self, screen_path: str, template_name: str, threshold: Optional[float] = None):
        match_threshold = self._resolve_threshold(template_name, threshold)
        best = self.find_best(screen_path, template_name)

        if best["score"] < match_threshold:
            raise SoftFail(
                f"Template '{template_name}' below threshold ({best['score']:.3f} < {match_threshold:.3f})"
            )
        return best

    def click_template(
        self,
        capture_fn: Callable[[], str],
        adb: object,
        template_name: str,
        threshold: Optional[float] = None,
        logger: Optional[logging.Logger] = None,
    ) -> dict[str, object]:
        screen_path = capture_fn()
        result = self.match_template(screen_path, template_name=template_name, threshold=threshold)
        center_x, center_y = result["center"]
        adb.tap(center_x, center_y)
        (logger or logging.getLogger(__name__)).info(
            "click_template(%s): confidence=%.3f coords=(%d,%d)",
            template_name,
            result["score"],
            center_x,
            center_y,
        )
        return result

    def wait_for(
        self,
        capture_fn: Callable[[], str],
        template_name: str,
        timeout_s: int = 15,
        interval_s: float = 0.5,
        threshold: Optional[float] = None,
    ) -> dict[str, object]:
        deadline = time.monotonic() + timeout_s
        last_error: Optional[Exception] = None

        while time.monotonic() < deadline:
            screen_path = capture_fn()
            try:
                return self.match_template(screen_path, template_name, threshold=threshold)
            except SoftFail as exc:
                last_error = exc
                time.sleep(interval_s)

        raise SoftFail(f"Timeout waiting for template '{template_name}': {last_error}")

    def wait_and_click(
        self,
        capture_fn: Callable[[], str],
        adb: object,
        template_name: str,
        timeout_s: int = 15,
        interval_s: float = 0.5,
        threshold: Optional[float] = None,
        logger: Optional[logging.Logger] = None,
        jitter_px: int = 0,
        post_sleep_s: float = 0.15,
    ) -> dict[str, object]:
        result = self.wait_for(
            capture_fn,
            template_name=template_name,
            timeout_s=timeout_s,
            interval_s=interval_s,
            threshold=threshold,
        )
        center_x, center_y = result["center"]
        if jitter_px > 0:
            center_x += random.randint(-jitter_px, jitter_px)
            center_y += random.randint(-jitter_px, jitter_px)
        adb.tap(center_x, center_y)
        (logger or logging.getLogger(__name__)).info(
            "wait_and_click(%s): confidence=%.3f coords=(%d,%d) jitter=%d",
            template_name,
            result["score"],
            center_x,
            center_y,
            jitter_px,
        )
        if post_sleep_s > 0:
            time.sleep(post_sleep_s)
        return result