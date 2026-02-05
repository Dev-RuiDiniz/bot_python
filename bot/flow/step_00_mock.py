"""Mock step for bootstrap validation (DIA 1)."""

from __future__ import annotations

import time

from bot.flow.step_base import Step, StepContext


class Step00Mock(Step):
    name = "step_00_mock"

    def run(self, context: StepContext) -> None:
        context.logger.info("Executando passo mock para %s", context.instance_id)
        time.sleep(0.5)
        context.logger.info("Passo mock finalizado")
