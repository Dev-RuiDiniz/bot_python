"""Run one bot instance end-to-end."""

from __future__ import annotations

from typing import Any, Iterable

from bot.config.loader import InstanceConfig
from bot.core.adb import ADBClient
from bot.core.exceptions import CriticalFail, SoftFail
from bot.core.logger import setup_instance_logger
from bot.core.vision import Vision
from bot.flow.step_00_mock import Step00Mock
from bot.flow.step_base import Step, StepContext


def default_steps() -> Iterable[Step]:
    return [Step00Mock()]


def run_instance(instance: InstanceConfig, bot_config: dict[str, Any]) -> int:
    logger = setup_instance_logger(instance.instance_id, logs_dir=bot_config.get("logs_dir", "logs"))
    adb = ADBClient(serial=instance.serial, adb_bin=bot_config.get("adb_bin", "adb"))
    vision = Vision(templates_dir=bot_config.get("templates_dir", "bot/assets/templates"))
    context = StepContext(
        instance_id=instance.instance_id,
        adb=adb,
        vision=vision,
        logger=logger,
        config=bot_config,
    )

    try:
        logger.info("Iniciando instância %s", instance.instance_id)
        adb.connect()
        adb.start_app(instance.app_package, instance.app_activity)

        for step in default_steps():
            logger.info("Executando %s", step)
            try:
                step.run(context)
            except SoftFail as exc:
                logger.warning("SoftFail em %s: %s", step, exc)

        logger.info("Instância %s finalizada", instance.instance_id)
        return 0
    except CriticalFail as exc:
        logger.error("CriticalFail em %s: %s", instance.instance_id, exc)
        return 2
    finally:
        try:
            adb.stop_app(instance.app_package)
        except CriticalFail as exc:
            logger.warning("Falha ao encerrar app: %s", exc)
