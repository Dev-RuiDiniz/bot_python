"""Step 04: Amigos flow with bounded gift interaction loop."""

from __future__ import annotations

from pathlib import Path
from time import monotonic

from bot.core.exceptions import CriticalFail, SoftFail
from bot.core.template_ids import (
    T_AMIGOS_ENVIAR,
    T_AMIGOS_ENTRAR,
    T_AMIGOS_RECOLHER,
    T_AMIGOS_SEM_PRESENTES,
    T_AMIGOS_TELA,
    T_HOME_SCREEN,
)
from bot.flow.recovery import recover_to_home
from bot.flow.step_base import Step, StepContext


class Step04Amigos(Step):
    name = "step_04_amigos"

    def run(self, context: StepContext) -> None:
        screenshot_path = Path("runtime") / context.instance_id / f"{self.name}.png"
        cfg = context.config.get("step_04", {})
        cycles = int(cfg.get("cycles", 3))
        timeout_enter = int(cfg.get("timeout_enter", 8))
        timeout_loop = int(cfg.get("timeout_loop", 8))
        max_interactions = int(cfg.get("max_interactions", 20))
        enter_retries = int(cfg.get("enter_retries", 2))
        jitter_px = int(cfg.get("click_jitter_px", 0))

        stats = context.metrics.setdefault(
            self.name,
            {"cycles": 0, "collected": 0, "sent": 0, "interactions": 0, "enter_attempts": 0},
        )

        def capture() -> str:
            return str(context.adb.screencap(str(screenshot_path)))

        for cycle in range(1, cycles + 1):
            stats["cycles"] += 1
            context.logger.info("[inst=%s][step=%s][cycle=%d] Entrando em Amigos", context.instance_id, self.name, cycle)

            if not self._enter_amigos(context, capture, timeout_enter, enter_retries, jitter_px, stats):
                raise SoftFail(f"{self.name}: não foi possível abrir Amigos no ciclo {cycle}")

            self._loop_presentes(context, capture, timeout_loop, max_interactions, jitter_px, stats, cycle)

            if not recover_to_home(context, capture, back_limit=3):
                raise CriticalFail(f"{self.name}: travado fora da Home após ciclo {cycle}")

    def _enter_amigos(self, context: StepContext, capture, timeout_enter: int, enter_retries: int, jitter_px: int, stats: dict) -> bool:
        for attempt in range(1, enter_retries + 1):
            stats["enter_attempts"] += 1
            try:
                context.vision.wait_and_click(
                    capture,
                    context.adb,
                    T_AMIGOS_ENTRAR,
                    timeout_s=timeout_enter,
                    threshold=0.88,
                    logger=context.logger,
                    jitter_px=jitter_px,
                )
                context.vision.wait_for(capture, T_AMIGOS_TELA, timeout_s=timeout_enter, threshold=0.88)
                context.logger.info(
                    "[inst=%s][step=%s][attempt=%d] Tela Amigos confirmada",
                    context.instance_id,
                    self.name,
                    attempt,
                )
                return True
            except SoftFail as exc:
                context.logger.warning(
                    "[inst=%s][step=%s][attempt=%d] Falha ao entrar em Amigos: %s",
                    context.instance_id,
                    self.name,
                    attempt,
                    exc,
                )
                recover_to_home(context, capture, back_limit=2)
        return False

    def _loop_presentes(self, context: StepContext, capture, timeout_loop: int, max_interactions: int, jitter_px: int, stats: dict, cycle: int) -> None:
        deadline = monotonic() + timeout_loop
        while monotonic() < deadline and stats["interactions"] < max_interactions:
            screen = capture()
            if context.vision.exists(screen, T_AMIGOS_SEM_PRESENTES, threshold=0.88):
                context.logger.info("[inst=%s][step=%s][cycle=%d] Sem presentes restantes", context.instance_id, self.name, cycle)
                return

            if context.vision.exists(screen, T_AMIGOS_RECOLHER, threshold=0.88):
                context.vision.wait_and_click(
                    capture,
                    context.adb,
                    T_AMIGOS_RECOLHER,
                    timeout_s=2,
                    threshold=0.88,
                    logger=context.logger,
                    jitter_px=jitter_px,
                )
                stats["collected"] += 1
                stats["interactions"] += 1
                continue

            if context.vision.exists(screen, T_AMIGOS_ENVIAR, threshold=0.88):
                context.vision.wait_and_click(
                    capture,
                    context.adb,
                    T_AMIGOS_ENVIAR,
                    timeout_s=2,
                    threshold=0.88,
                    logger=context.logger,
                    jitter_px=jitter_px,
                )
                stats["sent"] += 1
                stats["interactions"] += 1
                continue

            if context.vision.exists(screen, T_HOME_SCREEN, threshold=0.88):
                raise CriticalFail(f"{self.name}: saiu inesperadamente de Amigos para Home durante loop")

            break

        if stats["interactions"] >= max_interactions:
            context.logger.warning(
                "[inst=%s][step=%s][cycle=%d] max_interactions atingido (%d)",
                context.instance_id,
                self.name,
                cycle,
                max_interactions,
            )
