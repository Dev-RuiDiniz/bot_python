"""Run one bot instance end-to-end."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from bot.config.loader import InstanceConfig
from bot.core.adb import ADBClient
from bot.core.exceptions import CriticalFail, SoftFail
from bot.core.logger import setup_instance_logger
from bot.core.vision import Vision
from bot.flow.step_01_home import Step01Home
from bot.flow.step_02_roleta import Step02Roleta
from bot.flow.step_03_confirm_home import Step03ConfirmHome
from bot.flow.step_base import Step, StepContext


def default_steps() -> Iterable[Step]:
    return [Step01Home(), Step02Roleta(), Step03ConfirmHome()]


def _snapshot_failure(context: StepContext, step_name: str, attempt: int | None = None) -> None:
    logs_dir = context.config.get("logs_dir", "logs")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    attempt_label = attempt if attempt is not None else context.config.get("current_attempt", "na")
    snapshot_path = (
        Path(logs_dir)
        / "snapshots"
        / context.instance_id
        / f"{timestamp}_{context.instance_id}_{step_name}_attempt{attempt_label}.png"
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


def run_instance(instance: InstanceConfig, bot_config: dict[str, Any]) -> int:
    logger = setup_instance_logger(instance.instance_id, logs_dir=bot_config.get("logs_dir", "logs"))
    adb = ADBClient(serial=instance.serial, adb_bin=bot_config.get("adb_bin", "adb"))
    vision = Vision(
        templates_dir=bot_config.get("templates_dir", "bot/assets/templates"),
        template_map=bot_config.get("templates", {}),
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
    )
    current_step = "bootstrap"

    try:
        logger.info("Iniciando instância %s", instance.instance_id)
        adb.connect()
        for step in default_steps():
            current_step = step.name
            logger.info("Executando %s", step)
            try:
                step.run(context)
            except SoftFail as exc:
                logger.warning("SoftFail em %s: %s", step, exc)

        logger.info("Instância %s finalizada", instance.instance_id)
        return 0
    except CriticalFail as exc:
        logger.error("CriticalFail em %s: %s", instance.instance_id, exc)
        _snapshot_failure(context, current_step)
        return 2
    except Exception as exc:  # noqa: BLE001
        logger.exception("Erro inesperado em %s: %s", instance.instance_id, exc)
        _snapshot_failure(context, current_step)
        return 3
    finally:
        _safe_shutdown(context, instance)
