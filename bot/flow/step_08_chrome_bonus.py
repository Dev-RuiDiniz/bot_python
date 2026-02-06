"""Step 08: abrir Chrome e validar página de bônus."""

from __future__ import annotations

from pathlib import Path

from bot.core.exceptions import CriticalFail, Reason, SoftFail
from bot.core.template_ids import T_CHROME_BARRA_ENDERECO, T_CHROME_CAPTCHA, T_CHROME_PAGINA_BONUS
from bot.flow.step_base import Step, StepContext


class Step08ChromeBonus(Step):
    name = "step_08_chrome_bonus"

    def run(self, context: StepContext) -> None:
        screenshot_path = Path("runtime") / context.instance_id / f"{self.name}.png"
        cfg = context.config.get("step_08", {})
        timeout_s = int(cfg.get("timeout_page", 12))
        bonus_url = str(cfg.get("bonus_url", context.config.get("bonus_url", "https://example.com/bonus")))
        navigation_mode = str(cfg.get("navigation_mode", "intent"))

        def capture() -> str:
            return str(context.adb.screencap(str(screenshot_path)))

        context.adb.start_app(
            context.config.get("chrome_package", "com.android.chrome"),
            context.config.get("chrome_activity", "com.google.android.apps.chrome.Main"),
        )

        if navigation_mode == "input_text":
            context.vision.wait_and_click(capture, context.adb, T_CHROME_BARRA_ENDERECO, timeout_s=timeout_s, logger=context.logger)
            context.adb.input_text(bonus_url)
            context.adb.keyevent(66)
        else:
            context.adb.open_url(bonus_url)

        try:
            context.vision.wait_for(capture, T_CHROME_PAGINA_BONUS, timeout_s=timeout_s)
        except SoftFail as exc:
            if context.vision.exists(capture(), T_CHROME_CAPTCHA):
                raise CriticalFail(f"{self.name}: captcha detectado", reason=Reason.CAPTCHA_DETECTED) from exc
            raise CriticalFail(f"{self.name}: página bônus não carregou", reason=Reason.BONUS_PAGE_NOT_FOUND) from exc
