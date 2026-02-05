"""Step 01: ensure app home is visible."""

from __future__ import annotations

from pathlib import Path

from bot.flow.step_base import Step, StepContext


class Step01Home(Step):
    name = "step_01_home"

    def run(self, context: StepContext) -> None:
        screenshot_path = Path("runtime") / context.instance_id / "step_01_home.png"

        def capture() -> str:
            return str(context.adb.screencap(str(screenshot_path)))

        template = context.config.get("templates", {}).get("home", "home.png")
        result = context.vision.wait_for(capture, template_name=template, timeout_s=10)
        context.logger.info("Home detectado com score %.3f em %s", result.score, result.center)
