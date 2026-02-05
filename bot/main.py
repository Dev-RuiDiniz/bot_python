"""CLI entrypoint for bot execution."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from bot.runner.instance_runner import InstanceConfig, run_instance
from bot.runner.multiprocess import run_parallel


def load_yaml(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML inválido para objeto raiz: {path}")
    return data


def parse_instances(config: dict) -> list[InstanceConfig]:
    instances = []
    for item in config.get("instances", []):
        instances.append(
            InstanceConfig(
                instance_id=item["id"],
                serial=item["serial"],
                app_package=item["app_package"],
                app_activity=item["app_activity"],
            )
        )
    return instances


def main() -> int:
    parser = argparse.ArgumentParser(description="Android bot runner")
    parser.add_argument("--bot-config", default="bot/config/bot.yaml")
    parser.add_argument("--instances-config", default="bot/config/instances.yaml")
    parser.add_argument("--parallel", action="store_true")
    args = parser.parse_args()

    bot_config = load_yaml(args.bot_config)
    instances_raw = load_yaml(args.instances_config)
    instances = parse_instances(instances_raw)

    if not instances:
        print("Nenhuma instância configurada.")
        return 1

    if args.parallel:
        codes = run_parallel(instances, bot_config)
        return 0 if all(code == 0 for code in codes) else 2

    code = 0
    for instance in instances:
        code = max(code, run_instance(instance, bot_config))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
