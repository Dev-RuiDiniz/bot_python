"""Step 05: Roleta principal com 2 giros e recuperação robusta."""

from __future__ import annotations

from pathlib import Path

from bot.core.exceptions import CriticalFail, SoftFail
from bot.core.template_ids import (
    T_RULETA_GIRAR,
    T_RULETA_PRINCIPAL,
    T_RULETA_RESULTADO,
    T_RULETA_SAIR,
)
from bot.flow.recovery import recover_to_home
from bot.flow.step_base import Step, StepContext


class Step05RoletaPrincipal(Step):
    name = "step_05_roleta_principal"

    def run(self, context: StepContext) -> None:
        screenshot_path = Path("runtime") / context.instance_id / f"{self.name}.png"
        cfg = context.config.get("step_05", {})
        spins = int(cfg.get("spins", 2))
        spin_timeout = int(cfg.get("spin_timeout", 6))
        result_timeout = int(cfg.get("result_timeout", 10))

        stats = context.metrics.setdefault(
            self.name,
            {"spins_done": 0, "timeouts": 0, "recoveries": 0},
        )

        def capture() -> str:
            return str(context.adb.screencap(str(screenshot_path)))

        context.logger.info("[inst=%s][step=%s] Entrando na Roleta Principal", context.instance_id, self.name)
        context.vision.wait_and_click(capture, context.adb, T_RULETA_PRINCIPAL, timeout_s=spin_timeout, logger=context.logger)
        context.vision.wait_for(capture, T_RULETA_GIRAR, timeout_s=spin_timeout)

        for spin_idx in range(1, spins + 1):
            try:
                context.logger.info("[inst=%s][step=%s][spin=%d] Iniciando giro", context.instance_id, self.name, spin_idx)
                context.vision.wait_and_click(capture, context.adb, T_RULETA_GIRAR, timeout_s=spin_timeout, logger=context.logger)
                context.vision.wait_for(capture, T_RULETA_RESULTADO, timeout_s=result_timeout)
                stats["spins_done"] += 1
            except SoftFail as exc:
                stats["timeouts"] += 1
                context.logger.warning("[inst=%s][step=%s][spin=%d] SoftFail no giro: %s", context.instance_id, self.name, spin_idx, exc)
                self._leave_roleta(context, capture, stats)
                raise SoftFail(f"{self.name}: giro {spin_idx} falhou ({exc})") from exc

        self._leave_roleta(context, capture, stats)

    def _leave_roleta(self, context: StepContext, capture, stats: dict[str, int]) -> None:
        try:
            context.vision.wait_and_click(capture, context.adb, T_RULETA_SAIR, timeout_s=3, logger=context.logger)
        except SoftFail:
            context.logger.info("[inst=%s][step=%s] Botão sair da roleta não encontrado", context.instance_id, self.name)

        if not recover_to_home(context, capture, back_limit=3):
            stats["recoveries"] += 1
            raise CriticalFail(f"{self.name}: não recuperou para Home após roleta")
        stats["recoveries"] += 1
