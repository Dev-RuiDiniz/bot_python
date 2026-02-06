"""Step 02: initial roulette skeleton (optional availability)."""

from __future__ import annotations

from pathlib import Path

from bot.core.exceptions import SoftFail
from bot.core.template_ids import T_RULETA_AVAILABLE, T_RULETA_BUTTON, T_RULETA_CLOSE
from bot.flow.step_base import Step, StepContext


class Step02Roleta(Step):
    name = "step_02_roleta"

    def run(self, context: StepContext) -> None:
        screenshot_path = Path("runtime") / context.instance_id / "step_02_roleta.png"

        def capture() -> str:
            return str(context.adb.screencap(str(screenshot_path)))

        screen_path = capture()
        if not context.vision.exists(screen_path, T_RULETA_AVAILABLE, threshold=0.88):
            raise SoftFail("Roleta indisponível no momento (skeleton default)")

        context.logger.info("[inst=%s][step=%s][attempt=1] Roleta disponível, executando giro único", context.instance_id, self.name)
        context.vision.click_template(capture, context.adb, T_RULETA_BUTTON, threshold=0.88, logger=context.logger)
        context.vision.click_template(capture, context.adb, T_RULETA_CLOSE, threshold=0.88, logger=context.logger)
