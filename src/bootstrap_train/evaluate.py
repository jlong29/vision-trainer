from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .train import build_yolo_command, load_config, run_command
from .validate_packages import validate_phase1_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch a config-driven Ultralytics evaluation run.")
    parser.add_argument("--config", required=True, help="Evaluation config YAML.")
    parser.add_argument("--dataset-root", required=True, help="Phase 1 package root.")
    parser.add_argument("--weights", required=True, help="Path to weights/checkpoint file.")
    parser.add_argument("--device", help="Override the configured device selection.")
    parser.add_argument("--name", help="Override the configured run name.")
    parser.add_argument("--project", help="Override the configured project directory.")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it.")
    return parser


def prepare_evaluation_command(
    config_path: str | Path,
    dataset_root: str | Path,
    weights: str | Path,
    device: str | None = None,
    name: str | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    package_root = Path(dataset_root)
    validation = validate_phase1_package(package_root)
    if not validation.ok:
        raise ValueError("phase 1 package validation failed")

    options: dict[str, Any] = {key: value for key, value in config.items() if key not in {"task", "mode"}}
    options["data"] = str((package_root / "dataset.yaml").resolve())
    options["model"] = str(Path(weights).resolve())
    if device:
        options["device"] = device
    if name:
        options["name"] = name
    if project:
        options["project"] = project

    command = build_yolo_command(str(config.get("task", "detect")), str(config.get("mode", "val")), options)
    return {
        "command": command,
        "config": config,
        "validation": validation.to_dict(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    prepared = prepare_evaluation_command(
        args.config,
        dataset_root=args.dataset_root,
        weights=args.weights,
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
