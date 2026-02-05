"""CLI entrypoint for bot execution."""

from __future__ import annotations

import argparse

from bot.config.loader import InstanceConfig, load_bot_config, load_instances_config
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
