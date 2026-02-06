"""Reusable recovery helpers for returning the app to Home state."""

from __future__ import annotations

import time
from typing import Callable

from bot.core.exceptions import SoftFail
from bot.flow.step_base import StepContext


def recover_to_home(context: StepContext, capture_fn: Callable[[], str], back_limit: int = 3) -> bool:
    context.logger.info("Recovery para home iniciado (limite BACK=%d)", back_limit)
    for _ in range(back_limit):
        context.adb.keyevent(4)  # KEYCODE_BACK
        time.sleep(0.4)
        screen_path = capture_fn()
        if context.vision.exists(screen_path, "home.tela_home", threshold=0.88):
            context.logger.info("Recovery concluiu em home via BACK")
            return True

    try:
        context.vision.click_template(
            capture_fn=capture_fn,
            adb=context.adb,
            template_name="home.botao_home",
            threshold=0.88,
            logger=context.logger,
        )
        time.sleep(0.4)
        screen_path = capture_fn()
        if context.vision.exists(screen_path, "home.tela_home", threshold=0.88):
            context.logger.info("Recovery concluiu em home via botão")
            return True
    except SoftFail:
        context.logger.info("Template opcional home.botao_home não encontrado durante recovery")

    return False
