"""Config loader utilities for bot YAML files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class BotConfig:
    adb_bin: str = "adb"
    templates_dir: str = "bot/assets/templates"
    logs_dir: str = "logs"
    templates: dict[str, str] | None = None
    chrome_package: str = "com.android.chrome"
    vpn_package: str = "com.vpn.app"
    step_01: dict[str, Any] | None = None
    step_03: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "BotConfig":
        return cls(
            adb_bin=raw.get("adb_bin", "adb"),
            templates_dir=raw.get("templates_dir", "bot/assets/templates"),
            logs_dir=raw.get("logs_dir", "logs"),
            templates=raw.get("templates", {}) or {},
            chrome_package=raw.get("chrome_package", "com.android.chrome"),
            vpn_package=raw.get("vpn_package", "com.vpn.app"),
            step_01=raw.get("step_01", {}) or {},
            step_03=raw.get("step_03", {}) or {},
        )


@dataclass(slots=True)
class InstanceConfig:
    instance_id: str
    serial: str
    app_package: str
    app_activity: str


@dataclass(slots=True)
class InstancesConfig:
    instances: list[InstanceConfig]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "InstancesConfig":
        instances = [
            InstanceConfig(
                instance_id=item["id"],
                serial=item["serial"],
                app_package=item["app_package"],
                app_activity=item["app_activity"],
            )
            for item in raw.get("instances", [])
        ]
        return cls(instances=instances)


def load_yaml(path: str | Path) -> dict[str, Any]:
    yaml_path = Path(path)
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML não instalado. Instale com: pip install pyyaml") from exc

    with yaml_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML inválido para objeto raiz: {yaml_path}")
    return data


def load_bot_config(path: str | Path) -> BotConfig:
    return BotConfig.from_dict(load_yaml(path))


def load_instances_config(path: str | Path) -> InstancesConfig:
    return InstancesConfig.from_dict(load_yaml(path))
