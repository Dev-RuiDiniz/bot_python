"""Step 07: validar conexão VPN antes do bônus."""

from __future__ import annotations

from pathlib import Path

from bot.core.exceptions import CriticalFail, Reason, SoftFail
from bot.core.template_ids import T_VPN_CONECTADA, T_VPN_CONECTAR, T_VPN_DESCONECTADA, T_VPN_ERRO
from bot.flow.step_base import Step, StepContext


class Step07VPN(Step):
    name = "step_07_vpn"

    def run(self, context: StepContext) -> None:
        screenshot_path = Path("runtime") / context.instance_id / f"{self.name}.png"
        cfg = context.config.get("step_07", {})
        timeout_s = int(cfg.get("timeout_connect", 10))

        def capture() -> str:
            return str(context.adb.screencap(str(screenshot_path)))

        stats = context.metrics.setdefault(self.name, {"already_connected": 0, "connect_clicks": 0})

        if context.vision.exists(capture(), T_VPN_CONECTADA):
            stats["already_connected"] += 1
            return

        if context.vision.exists(capture(), T_VPN_DESCONECTADA):
            context.vision.wait_and_click(capture, context.adb, T_VPN_CONECTAR, timeout_s=timeout_s, logger=context.logger)
            stats["connect_clicks"] += 1

        try:
            context.vision.wait_for(capture, T_VPN_CONECTADA, timeout_s=timeout_s)
        except SoftFail as exc:
            if context.vision.exists(capture(), T_VPN_ERRO):
                raise CriticalFail(f"{self.name}: erro ao conectar VPN", reason=Reason.VPN_ERROR) from exc
            raise CriticalFail(f"{self.name}: timeout aguardando VPN conectada", reason=Reason.VPN_TIMEOUT) from exc
