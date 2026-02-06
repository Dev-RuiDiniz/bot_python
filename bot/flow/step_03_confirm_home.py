"""Step 03: confirm app can recover back to Home state."""

from __future__ import annotations

from pathlib import Path

from bot.core.exceptions import CriticalFail
from bot.flow.recovery import recover_to_home
from bot.flow.step_base import Step, StepContext


class Step03ConfirmHome(Step):
    name = "step_03_confirm_home"

    def run(self, context: StepContext) -> None:
        screenshot_path = Path("runtime") / context.instance_id / "step_03_confirm_home.png"

        def capture() -> str:
            return str(context.adb.screencap(str(screenshot_path)))

        back_limit = int(context.config.get("step_03", {}).get("recovery_back_limit", 3))
        if not recover_to_home(context, capture, back_limit=back_limit):
            raise CriticalFail("step_03_confirm_home: não foi possível confirmar Home")
        context.logger.info("[inst=%s][step=%s][attempt=1] Home confirmada", context.instance_id, self.name)
