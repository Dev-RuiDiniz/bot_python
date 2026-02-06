"""Run one bot instance end-to-end."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from time import monotonic
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
from bot.flow.step_base import Step, StepContext


def default_steps() -> Iterable[Step]:
    return [Step01Home(), Step02Roleta(), Step03ConfirmHome(), Step04Amigos(), Step05RoletaPrincipal(), Step06NokoBox()]


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
    context.logger.info("Iniciando safe shutdown (best effort)")
    packages_to_stop = [
        instance.app_package,
        context.config.get("chrome_package", "com.android.chrome"),
        context.config.get("vpn_package", "com.vpn.app"),
    ]
    for package in packages_to_stop:
        try:
            context.adb.stop_app(package)
            context.logger.info("Safe shutdown: app encerrado (%s)", package)
        except Exception as exc:  # noqa: BLE001 - best effort shutdown
            context.logger.warning("Safe shutdown: falha ao encerrar %s (%s)", package, exc)


def _make_run_id() -> str:
    return f"{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:4]}"


def run_instance(instance: InstanceConfig, bot_config: dict[str, Any]) -> int:
    run_id = _make_run_id()
    logger = setup_instance_logger(instance.instance_id, run_id=run_id, logs_dir=bot_config.get("logs_dir", "logs"))
    adb = ADBClient(serial=instance.serial, adb_bin=bot_config.get("adb_bin", "adb"))
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
    current_step = "bootstrap"
    started_at = monotonic()

    try:
        logger.info("Iniciando instância %s", instance.instance_id)
        adb.connect()
        for step in default_steps():
            current_step = step.name
            logger.info("Executando %s", step)
            try:
                step.run(context)
                context.metrics.setdefault("steps", {})[step.name] = "ok"
            except SoftFail as exc:
                context.metrics.setdefault("steps", {})[step.name] = f"soft_fail: {exc}"
                logger.warning("SoftFail em %s: %s", step, exc)

        logger.info("Instância %s finalizada", instance.instance_id)
        return 0
    except CriticalFail as exc:
        logger.error("CriticalFail em %s: %s", instance.instance_id, exc)
        _snapshot_failure(context, current_step)
        context.metrics.setdefault("steps", {})[current_step] = f"critical_fail: {exc}"
        return 2
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
            "Resumo final | run_id=%s | steps=%s | amigos(collected=%s,sent=%s,interactions=%s,enter_attempts=%s) | roleta(spins_done=%s,timeouts=%s,recoveries=%s) | noko(opened=%s,empty=%s,collected=%s,recoveries=%s) | tempo_total=%.2fs",
            run_id,
            context.metrics.get("steps", {}),
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
