"""Step 10: finalização da instância com parada do app e status final."""

from __future__ import annotations

from pathlib import Path

from bot.core.exceptions import SoftFail
from bot.core.template_ids import T_HOME_SCREEN
from bot.flow.recovery import recover_to_home
from bot.flow.step_base import Step, StepContext


class Step10Finalize(Step):
    name = "step_10_finalize"

    def run(self, context: StepContext) -> None:
        screenshot_path = Path("runtime") / context.instance_id / f"{self.name}.png"

        def capture() -> str:
            return str(context.adb.screencap(str(screenshot_path)))

        if not context.vision.exists(capture(), T_HOME_SCREEN, threshold=0.88):
            recover_to_home(context, capture, back_limit=3)

        if not context.vision.exists(capture(), T_HOME_SCREEN, threshold=0.88):
            raise SoftFail(f"{self.name}: não foi possível garantir Home antes de finalizar")

        context.adb.stop_app(context.config["app_package"])
        context.metrics["finished"] = True
        context.logger.info("[inst=%s][step=%s] Instância finalizada com sucesso", context.instance_id, self.name)
