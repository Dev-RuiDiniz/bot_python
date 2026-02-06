"""Step 09: voltar ao jogo e coletar bônus com recuperação para Home."""

from __future__ import annotations

from pathlib import Path

from bot.core.exceptions import SoftFail
from bot.core.template_ids import T_BONUS_BOTAO_DISPONIVEL, T_BONUS_COLETADO, T_BONUS_INDISPONIVEL
from bot.flow.recovery import recover_to_home
from bot.flow.step_base import Step, StepContext


class Step09BonusCollect(Step):
    name = "step_09_bonus_collect"

    def run(self, context: StepContext) -> None:
        screenshot_path = Path("runtime") / context.instance_id / f"{self.name}.png"
        cfg = context.config.get("step_09", {})
        timeout_s = int(cfg.get("timeout_bonus", 8))

        stats = context.metrics.setdefault(self.name, {"collected": 0, "unavailable": 0, "softfails": 0})

        def capture() -> str:
            return str(context.adb.screencap(str(screenshot_path)))

        context.adb.start_app(context.config["app_package"], context.config["app_activity"])

        try:
            if context.vision.exists(capture(), T_BONUS_BOTAO_DISPONIVEL):
                context.vision.wait_and_click(
                    capture,
                    context.adb,
                    T_BONUS_BOTAO_DISPONIVEL,
                    timeout_s=timeout_s,
                    logger=context.logger,
                )
                context.vision.wait_for(capture, T_BONUS_COLETADO, timeout_s=timeout_s)
                stats["collected"] += 1
                return

            if context.vision.exists(capture(), T_BONUS_INDISPONIVEL):
                stats["unavailable"] += 1
                context.logger.info("[inst=%s][step=%s] Bônus indisponível no momento", context.instance_id, self.name)
                return

            stats["softfails"] += 1
            raise SoftFail(f"{self.name}: nenhum indicador de bônus encontrado")
        finally:
            recover_to_home(context, capture, back_limit=3)
