"""OpenCV helpers for template matching and state waiting."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Optional

from bot.core.exceptions import SoftFail

try:
    import cv2
except ImportError:  # pragma: no cover - dependency may be optional in bootstrap phase
    cv2 = None


class Vision:
    def __init__(self, templates_dir: str) -> None:
        self.templates_dir = Path(templates_dir)
        self._templates: dict[str, object] = {}

    def _ensure_cv2(self) -> None:
        if cv2 is None:
            raise SoftFail("opencv-python is required for vision operations")

    def load_template(self, name: str):
        self._ensure_cv2()
        if name in self._templates:
            return self._templates[name]

        path = self.templates_dir / name
        if not path.exists():
            raise SoftFail(f"Template not found: {path}")
        template = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if template is None:
            raise SoftFail(f"Unable to read template: {path}")
        self._templates[name] = template
        return template

    def exists(self, screen_path: str, template_name: str, threshold: float = 0.90) -> bool:
        try:
            self.match_template(screen_path, template_name, threshold=threshold)
            return True
        except SoftFail:
            return False

    def match_template(self, screen_path: str, template_name: str, threshold: float = 0.90):
        self._ensure_cv2()
        screen = cv2.imread(screen_path, cv2.IMREAD_COLOR)
        if screen is None:
            raise SoftFail(f"Unable to read screenshot: {screen_path}")

        template = self.load_template(template_name)
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val < threshold:
            raise SoftFail(
                f"Template '{template_name}' below threshold ({max_val:.3f} < {threshold:.3f})"
            )

        h, w = template.shape[:2]
        return {
            "score": float(max_val),
            "center": (max_loc[0] + w // 2, max_loc[1] + h // 2),
        }

    def wait_for(
        self,
        capture_fn: Callable[[], str],
        template_name: str,
        timeout_s: int = 15,
        interval_s: float = 0.5,
        threshold: float = 0.90,
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
