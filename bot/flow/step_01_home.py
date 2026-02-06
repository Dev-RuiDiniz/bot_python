"""Step 01: ensure app home is visible."""

from __future__ import annotations

from pathlib import Path
import time

from bot.core.exceptions import CriticalFail, SoftFail
from bot.core.template_ids import T_ERROR_APP_CRASH, T_ERROR_CONN, T_HOME_SCREEN
from bot.flow.recovery import recover_to_home
from bot.flow.step_base import Step, StepContext


class Step01Home(Step):
    name = "step_01_home"

    def run(self, context: StepContext) -> None:
        screenshot_path = Path("runtime") / context.instance_id / "step_01_home.png"
        step_cfg = context.config.get("step_01", {})
        max_attempts = int(step_cfg.get("max_attempts", 3))
        timeout_s = int(step_cfg.get("home_timeout_s", 12))
        retries_back = int(step_cfg.get("recovery_back_limit", 3))

        def capture() -> str:
            return str(context.adb.screencap(str(screenshot_path)))

        for attempt in range(1, max_attempts + 1):
            context.logger.info(
                "[inst=%s][step=%s][attempt=%d] Tentativa %d/%d para validar home",
                context.instance_id,
                self.name,
                attempt,
                attempt,
                max_attempts,
            )
            context.adb.start_app(context.config["app_package"], context.config["app_activity"])
            try:
                result = context.vision.wait_for(capture, template_name=T_HOME_SCREEN, timeout_s=timeout_s)
                context.logger.info(
                    "[inst=%s][step=%s][attempt=%d] Home detectado com score %.3f em %s",
                    context.instance_id,
                    self.name,
                    attempt,
                    result["score"],
                    result["center"],
                )
                return
            except SoftFail:
                context.logger.warning(
                    "[inst=%s][step=%s][attempt=%d] Home não detectada",
                    context.instance_id,
                    self.name,
                    attempt,
                )

            screen_path = capture()
            if context.vision.exists(screen_path, T_ERROR_CONN, threshold=0.88):
                context.logger.warning(
                    "[inst=%s][step=%s][attempt=%d] Popup de erro de conexão detectado; tentando fechar",
                    context.instance_id,
                    self.name,
                    attempt,
                )
                recover_to_home(context, capture, back_limit=retries_back)
                time.sleep(0.5)
                continue

            if context.vision.exists(screen_path, T_ERROR_APP_CRASH, threshold=0.88):
                context.logger.error(
                    "[inst=%s][step=%s][attempt=%d] Crash detectado; relançando app",
                    context.instance_id,
                    self.name,
                    attempt,
                )
                context.adb.stop_app(context.config["app_package"])
                time.sleep(0.5)
                continue

            recover_to_home(context, capture, back_limit=retries_back)

        raise CriticalFail(f"{self.name}: falha ao validar home após {max_attempts} tentativas")
