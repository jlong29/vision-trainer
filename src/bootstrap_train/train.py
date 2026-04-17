from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from .manifests import load_simple_yaml
from .validate_packages import validate_phase1_package


def load_config(path: str | Path) -> dict[str, Any]:
    config = load_simple_yaml(path)
    if not isinstance(config, dict):
        raise ValueError("config must be a mapping")
    return config


def stringify_cli_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def build_yolo_command(task: str, mode: str, options: dict[str, Any]) -> list[str]:
    command = ["yolo", task, mode]
    for key, value in options.items():
        if value is None:
            continue
        command.append(f"{key}={stringify_cli_value(value)}")
    return command


def run_command(command: list[str], dry_run: bool = False) -> int:
    if dry_run:
        print(json.dumps({"dry_run": True, "command": command}, indent=2))
        return 0
    completed = subprocess.run(command, check=False)
    return completed.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch a config-driven Ultralytics training run.")
    parser.add_argument("--config", required=True, help="Training config YAML.")
    parser.add_argument("--dataset-root", help="Phase 1 package root. Required unless config sets data=...")
    parser.add_argument("--device", help="Override the configured device selection.")
    parser.add_argument("--name", help="Override the configured run name.")
    parser.add_argument("--project", help="Override the configured project directory.")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it.")
    return parser


def resolve_dataset_root(config: dict[str, Any], dataset_root: str | None) -> Path:
    if dataset_root:
        return Path(dataset_root)

    data_path = config.get("data")
    if not data_path:
        raise ValueError("provide --dataset-root or set data in the config")
    return Path(str(data_path)).expanduser().resolve().parent


def prepare_training_command(
    config_path: str | Path,
    dataset_root: str | None = None,
    device: str | None = None,
    name: str | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    package_root = resolve_dataset_root(config, dataset_root)
    validation = validate_phase1_package(package_root)
    if not validation.ok:
        raise ValueError("phase 1 package validation failed")

    options = {key: value for key, value in config.items() if key not in {"task", "mode"}}
    options["data"] = str((package_root / "dataset.yaml").resolve())
    if device:
        options["device"] = device
    if name:
        options["name"] = name
    if project:
        options["project"] = project

    task = str(config.get("task", "detect"))
    mode = str(config.get("mode", "train"))
    command = build_yolo_command(task, mode, options)
    return {
        "command": command,
        "config": config,
        "validation": validation.to_dict(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    prepared = prepare_training_command(
        args.config,
        dataset_root=args.dataset_root,
        device=args.device,
        name=args.name,
        project=args.project,
    )

    if args.dry_run:
        print(json.dumps(prepared, indent=2, sort_keys=True))
        return 0

    return run_command(prepared["command"], dry_run=False)


if __name__ == "__main__":
    raise SystemExit(main())
