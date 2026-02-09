"""Run one bot instance end-to-end."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from time import monotonic, sleep
from typing import Any, Iterable
from uuid import uuid4

from bot.config.loader import InstanceConfig
from bot.core.adb import ADBClient
from bot.core.exceptions import CriticalFail, SoftFail
from bot.core.logger import setup_instance_logger
from bot.core.vision import Vision
from bot.flow.step_01_home import Step01Home
from bot.flow.step_02_roleta import Step02Roleta
from bot.flow.step_03_confirm_home import Step03ConfirmHome
from bot.flow.step_04_amigos import Step04Amigos
from bot.flow.step_05_roleta_principal import Step05RoletaPrincipal
from bot.flow.step_06_noko_box import Step06NokoBox
from bot.flow.step_07_vpn import Step07VPN
from bot.flow.step_08_chrome_bonus import Step08ChromeBonus
from bot.flow.step_09_bonus_collect import Step09BonusCollect
from bot.flow.step_10_finalize import Step10Finalize
from bot.flow.step_base import Step, StepContext


def default_steps() -> Iterable[Step]:
    return [
        Step01Home(),
        Step02Roleta(),
        Step03ConfirmHome(),
        Step04Amigos(),
        Step05RoletaPrincipal(),
        Step06NokoBox(),
        Step07VPN(),
        Step08ChromeBonus(),
        Step09BonusCollect(),
        Step10Finalize(),
    ]


def _snapshot_failure(context: StepContext, step_name: str, attempt: int | None = None) -> None:
    logs_dir = context.config.get("logs_dir", "logs")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    attempt_label = attempt if attempt is not None else context.config.get("current_attempt", "na")
    snapshot_path = (
        Path(logs_dir)
        / "snapshots"
        / context.instance_id
        / f"{timestamp}_{context.run_id}_{context.instance_id}_{step_name}_attempt{attempt_label}.png"
    )
    try:
        context.adb.screencap(str(snapshot_path))
        context.logger.error(
            "[inst=%s][step=%s][attempt=%s] Snapshot de falha salvo em %s",
            context.instance_id,
            step_name,
            attempt_label,
            snapshot_path,
        )
    except Exception as exc:  # noqa: BLE001 - best effort em falha crítica
        context.logger.warning("Não foi possível salvar snapshot de falha: %s", exc)


def _safe_shutdown(context: StepContext, instance: InstanceConfig) -> None:
    context.logger.info("Iniciando safe shutdown (com retry)")
    packages_to_stop = [
        instance.app_package,
        context.config.get("chrome_package", "com.android.chrome"),
        context.config.get("vpn_package", "com.vpn.app"),
    ]
    retries = int(context.config.get("shutdown_retries", 3))
    retry_delay_s = float(context.config.get("shutdown_retry_delay_s", 0.3))

    for package in packages_to_stop:
        stopped = False
        for attempt in range(1, retries + 1):
            try:
                context.adb.stop_app(package)
                context.logger.info("Safe shutdown: app encerrado (%s) na tentativa %d/%d", package, attempt, retries)
                stopped = True
                break
            except Exception as exc:  # noqa: BLE001 - best effort shutdown
                context.logger.warning(
                    "Safe shutdown: falha ao encerrar %s na tentativa %d/%d (%s)", package, attempt, retries, exc
                )
                sleep(retry_delay_s)
        if not stopped:
            context.logger.error("Safe shutdown: não foi possível encerrar %s após %d tentativas", package, retries)


def _make_run_id() -> str:
    return f"{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:4]}"


def _trip_breaker(context: StepContext, reason: str) -> None:
    context.metrics["breaker_tripped"] = True
    context.metrics["breaker_reason"] = reason


def run_instance(instance: InstanceConfig, bot_config: dict[str, Any]) -> int:
    run_id = _make_run_id()
    logger = setup_instance_logger(instance.instance_id, run_id=run_id, logs_dir=bot_config.get("logs_dir", "logs"))
    emulator_cfg = bot_config.get("emulator", {}) or {}
    memuc_path = emulator_cfg.get("path") if emulator_cfg.get("type") == "MEmu" else None
    adb = ADBClient(serial=instance.serial, adb_bin=bot_config.get("adb_bin", "adb"), memuc_path=memuc_path)
    vision = Vision(
        templates_dir=bot_config.get("templates_dir", "bot/assets/templates"),
        template_map=bot_config.get("templates", {}),
        default_confidence=float(bot_config.get("default_confidence", 0.90)),
        templates_confidence=bot_config.get("templates_confidence", {}) or {},
    )
    context_config = {
        **bot_config,
        "app_package": instance.app_package,
        "app_activity": instance.app_activity,
    }
    context = StepContext(
        instance_id=instance.instance_id,
        adb=adb,
        vision=vision,
        logger=logger,
        config=context_config,
        run_id=run_id,
    )
    context.metrics.setdefault("steps", {})
    context.metrics.setdefault("step_durations", {})
    context.metrics.setdefault("breaker_tripped", False)
    context.metrics.setdefault("critical_reason", "")
    context.metrics.setdefault("reasons_count", {})
    current_step = "bootstrap"
    started_at = monotonic()

    breaker_cfg = bot_config.get("breaker", {}) or {}
    soft_limit = int(breaker_cfg.get("softfails", 3))
    critical_limit = int(breaker_cfg.get("criticals", 1))
    softfails = 0
    criticals = 0

    try:
        logger.info("Iniciando instância %s", instance.instance_id)
        if not adb.launch_instance(timeout=120):
            raise CriticalFail("Falha ao iniciar instância do emulador")
        adb.connect()
        width, height = adb.get_screen_resolution()
        context.metrics["screen_resolution"] = f"{width}x{height}"
        logger.info("Resolução detectada da instância %s: %sx%s", instance.instance_id, width, height)
        for step in default_steps():
            if softfails >= soft_limit:
                _trip_breaker(context, f"softfails>={soft_limit}")
                logger.error("Circuit breaker acionado por softfails (%d)", softfails)
                break
            if criticals >= critical_limit:
                _trip_breaker(context, f"criticals>={critical_limit}")
                logger.error("Circuit breaker acionado por criticals (%d)", criticals)
                break

            current_step = step.name
            logger.info("Executando %s", step)
            step_started = monotonic()
            try:
                step.run(context)
                context.metrics["steps"][step.name] = "ok"
            except SoftFail as exc:
                softfails += 1
                reason_key = str(exc.reason)
                reasons = context.metrics.setdefault("reasons_count", {})
                reasons[reason_key] = reasons.get(reason_key, 0) + 1
                context.metrics["steps"][step.name] = f"soft_fail: {exc}"
                logger.warning("SoftFail em %s: %s", step, exc)
            except CriticalFail as exc:
                criticals += 1
                reason_key = str(exc.reason)
                reasons = context.metrics.setdefault("reasons_count", {})
                reasons[reason_key] = reasons.get(reason_key, 0) + 1
                context.metrics["critical_reason"] = str(exc.reason)
                context.metrics["steps"][step.name] = f"critical_fail: {exc}"
                logger.error("CriticalFail em %s: %s", step, exc)
                _snapshot_failure(context, current_step)
                if criticals >= critical_limit:
                    _trip_breaker(context, f"criticals>={critical_limit}")
                break
            finally:
                context.metrics["step_durations"][step.name] = round(monotonic() - step_started, 3)

        logger.info("Instância %s finalizada", instance.instance_id)
        if context.metrics.get("critical_reason"):
            return 2
        return 0
    except Exception as exc:  # noqa: BLE001
        logger.exception("Erro inesperado em %s: %s", instance.instance_id, exc)
        _snapshot_failure(context, current_step)
        context.metrics.setdefault("steps", {})[current_step] = f"error: {exc}"
        return 3
    finally:
        elapsed = monotonic() - started_at
        amigos = context.metrics.get("step_04_amigos", {})
        roleta = context.metrics.get("step_05_roleta_principal", {})
        noko = context.metrics.get("step_06_noko_box", {})
        logger.info(
            "Resumo final | run_id=%s | steps=%s | step_durations=%s | critical_reason=%s | reasons_count=%s | breaker_tripped=%s | breaker_reason=%s | finished=%s | amigos(collected=%s,sent=%s,interactions=%s,enter_attempts=%s) | roleta(spins_done=%s,timeouts=%s,recoveries=%s) | noko(opened=%s,empty=%s,collected=%s,recoveries=%s) | tempo_total=%.2fs",
            run_id,
            context.metrics.get("steps", {}),
            context.metrics.get("step_durations", {}),
            context.metrics.get("critical_reason", ""),
            context.metrics.get("reasons_count", {}),
            context.metrics.get("breaker_tripped", False),
            context.metrics.get("breaker_reason", ""),
            context.metrics.get("finished", False),
            amigos.get("collected", 0),
            amigos.get("sent", 0),
            amigos.get("interactions", 0),
            amigos.get("enter_attempts", 0),
            roleta.get("spins_done", 0),
            roleta.get("timeouts", 0),
            roleta.get("recoveries", 0),
            noko.get("opened", 0),
            noko.get("empty", 0),
            noko.get("collected", 0),
            noko.get("recoveries", 0),
            elapsed,
        )
        _safe_shutdown(context, instance)
