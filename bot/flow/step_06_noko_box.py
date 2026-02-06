"""Step 06: Noko Box (vazia vs não vazia) com saída segura para Home."""

from __future__ import annotations

from pathlib import Path

from bot.core.exceptions import CriticalFail
from bot.core.template_ids import T_NOKO_BOX, T_NOKO_SAIR, T_NOKO_TELA, T_NOKO_VAZIA
from bot.flow.recovery import recover_to_home
from bot.flow.step_base import Step, StepContext


class Step06NokoBox(Step):
    name = "step_06_noko_box"

    def run(self, context: StepContext) -> None:
        screenshot_path = Path("runtime") / context.instance_id / f"{self.name}.png"
        cfg = context.config.get("step_06", {})
        timeout_enter = int(cfg.get("timeout_enter", 6))
        timeout_collect = int(cfg.get("timeout_collect", 4))
        collect_clicks = int(cfg.get("collect_clicks", 2))

        stats = context.metrics.setdefault(
            self.name,
            {"opened": 0, "empty": 0, "collected": 0, "recoveries": 0},
        )

        def capture() -> str:
            return str(context.adb.screencap(str(screenshot_path)))

        context.vision.wait_and_click(capture, context.adb, T_NOKO_BOX, timeout_s=timeout_enter, logger=context.logger)
        context.vision.wait_for(capture, T_NOKO_TELA, timeout_s=timeout_enter)
        stats["opened"] += 1

        if context.vision.exists(capture(), T_NOKO_VAZIA):
            stats["empty"] += 1
        else:
            for _ in range(collect_clicks):
                context.vision.wait_and_click(capture, context.adb, T_NOKO_TELA, timeout_s=timeout_collect, logger=context.logger)
                stats["collected"] += 1

        context.vision.wait_and_click(capture, context.adb, T_NOKO_SAIR, timeout_s=timeout_enter, logger=context.logger)

        if not recover_to_home(context, capture, back_limit=3):
            stats["recoveries"] += 1
            raise CriticalFail(f"{self.name}: não recuperou para Home após Noko")
        stats["recoveries"] += 1
