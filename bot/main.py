"""CLI entrypoint for bot execution."""

from __future__ import annotations

import argparse

from bot.config.loader import InstanceConfig, load_bot_config, load_instances_config
from bot.core.dependency_check import validate_runtime_dependencies
from bot.runner.instance_runner import run_instance
from bot.runner.multiprocess import run_parallel


def fake_instances() -> list[InstanceConfig]:
    return [
        InstanceConfig("fake_01", "emulator-5554", "com.example.app", ".MainActivity"),
        InstanceConfig("fake_02", "emulator-5556", "com.example.app", ".MainActivity"),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Android bot runner")
    parser.add_argument("--bot-config", default="bot/config/bot.yaml")
    parser.add_argument("--instances-config", default="bot/config/instances.yaml")
    parser.add_argument("--parallel", action="store_true")
    parser.add_argument("--fake", action="store_true", help="Executa duas instâncias fake em paralelo")
    args = parser.parse_args()

    validate_runtime_dependencies()
    bot_config = load_bot_config(args.bot_config)
    instances = fake_instances() if args.fake else load_instances_config(args.instances_config).instances

    if not instances:
        print("Nenhuma instância configurada.")
        return 1

    bot_config_raw = {
        "adb_bin": bot_config.adb_bin,
        "templates_dir": bot_config.templates_dir,
        "logs_dir": bot_config.logs_dir,
        "templates": bot_config.templates or {},
        "default_confidence": bot_config.default_confidence,
        "templates_confidence": bot_config.templates_confidence or {},
        "chrome_package": bot_config.chrome_package,
        "vpn_package": bot_config.vpn_package,
        "breaker": bot_config.breaker or {},
        "shutdown_retries": bot_config.shutdown_retries,
        "shutdown_retry_delay_s": bot_config.shutdown_retry_delay_s,
        "chrome_activity": bot_config.chrome_activity,
        "bonus_url": bot_config.bonus_url,
        "step_01": bot_config.step_01 or {},
        "step_03": bot_config.step_03 or {},
        "step_04": bot_config.step_04 or {},
        "step_05": bot_config.step_05 or {},
        "step_06": bot_config.step_06 or {},
        "step_07": bot_config.step_07 or {},
        "step_08": bot_config.step_08 or {},
        "step_09": bot_config.step_09 or {},
        "step_10": bot_config.step_10 or {},
    }

    if args.parallel or args.fake:
        codes = run_parallel(instances, bot_config_raw)
        return 0 if all(code == 0 for code in codes) else 2

    code = 0
    for instance in instances:
        code = max(code, run_instance(instance, bot_config_raw))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
