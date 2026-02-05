"""Step 02: example interaction with roulette button."""

from __future__ import annotations

from pathlib import Path

from bot.flow.step_base import Step, StepContext


class Step02Roleta(Step):
    name = "step_02_roleta"

    def run(self, context: StepContext) -> None:
        screenshot_path = Path("runtime") / context.instance_id / "step_02_roleta.png"

        def capture() -> str:
            return str(context.adb.screencap(str(screenshot_path)))

        template = context.config.get("templates", {}).get("roleta", "roleta.png")
        result = context.vision.wait_for(capture, template_name=template, timeout_s=8)
        context.adb.tap(*result.center)
        context.logger.info("Roleta acionada em %s (score %.3f)", result.center, result.score)
