"""Dependency validation helpers used at startup."""

from __future__ import annotations


def validate_runtime_dependencies() -> None:
    missing: list[str] = []
    for package, module in (("PyYAML", "yaml"), ("opencv-python", "cv2"), ("numpy", "numpy")):
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        formatted = ", ".join(missing)
        raise RuntimeError(
            f"Dependências ausentes: {formatted}. Instale com: pip install -r requirements.txt"
        )
