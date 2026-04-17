from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .manifests import dump_json, iso_now
from .train import build_yolo_command, load_config, run_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch a config-driven Ultralytics export run.")
    parser.add_argument("--config", required=True, help="Export config YAML.")
    parser.add_argument("--weights", required=True, help="Path to source weights/checkpoint file.")
    parser.add_argument("--name", help="Override the configured export name.")
    parser.add_argument("--project", help="Override the configured export project directory.")
    parser.add_argument("--device", help="Override the configured export device.")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it.")
    return parser


def prepare_export_command(
    config_path: str | Path,
    weights: str | Path,
    name: str | None = None,
    project: str | None = None,
    device: str | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    options: dict[str, Any] = {key: value for key, value in config.items() if key not in {"task", "mode"}}
    options["model"] = str(Path(weights).resolve())
    if name:
        options["name"] = name
    if project:
        options["project"] = project
    if device:
        options["device"] = device

    task = str(config.get("task", "detect"))
    mode = str(config.get("mode", "export"))
    command = build_yolo_command(task, mode, options)
    export_dir = Path(str(options.get("project", "artifacts/exports"))) / str(options.get("name", "candidate_export"))
    return {
        "command": command,
        "config": config,
        "export_dir": str(export_dir),
        "weights": str(Path(weights).resolve()),
    }


def record_export_request(prepared: dict[str, Any]) -> None:
    export_dir = Path(prepared["export_dir"])
    payload = {
        "created_at": iso_now(),
        "weights": prepared["weights"],
        "command": prepared["command"],
        "config": prepared["config"],
    }
    dump_json(export_dir / "export_request.json", payload)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    prepared = prepare_export_command(
        args.config,
        weights=args.weights,
        name=args.name,
        project=args.project,
        device=args.device,
    )

    if args.dry_run:
        print(json.dumps(prepared, indent=2, sort_keys=True))
        return 0

    record_export_request(prepared)
    return run_command(prepared["command"], dry_run=False)


if __name__ == "__main__":
    raise SystemExit(main())
