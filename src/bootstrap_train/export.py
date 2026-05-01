from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .manifests import dump_json, iso_now
from .train import build_yolo_command, load_config, run_command
from .validate_packages import validate_curated_release


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch a config-driven Ultralytics export run.")
    parser.add_argument("--config", required=True, help="Export config YAML.")
    parser.add_argument("--weights", required=True, help="Path to source weights/checkpoint file.")
    parser.add_argument("--name", help="Override the configured export name.")
    parser.add_argument("--project", help="Override the configured export project directory.")
    parser.add_argument("--device", help="Override the configured export device.")
    parser.add_argument("--source-kind", choices=["phase1", "curated_release"], help="Dataset source kind for metadata.")
    parser.add_argument("--source-id", help="Dataset package_id or curated release_id for metadata.")
    parser.add_argument("--release-root", help="Curated release root to validate and record in export metadata.")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it.")
    return parser


def prepare_export_command(
    config_path: str | Path,
    weights: str | Path,
    name: str | None = None,
    project: str | None = None,
    device: str | None = None,
    source_kind: str | None = None,
    source_id: str | None = None,
    release_root: str | Path | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    options: dict[str, Any] = {
        key: value
        for key, value in config.items()
        if key not in {"task", "mode", "source_kind", "source_id", "release_root"}
    }
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
    selected_source_kind = source_kind or config.get("source_kind")
    selected_source_id = source_id or config.get("source_id")
    selected_release_root = release_root or config.get("release_root")
    source: dict[str, Any] = {}
    if selected_release_root:
        validation = validate_curated_release(selected_release_root)
        if not validation.ok:
            raise ValueError("curated_release validation failed")
        source = {
            "kind": "curated_release",
            "root": str(Path(selected_release_root).resolve()),
            "id": validation.details.get("release_id"),
            "details": validation.details,
            "validation": validation.to_dict(),
        }
    elif selected_source_kind or selected_source_id:
        source = {
            "kind": selected_source_kind,
            "id": selected_source_id,
        }

    prepared = {
        "command": command,
        "config": config,
        "export_dir": str(export_dir),
        "weights": str(Path(weights).resolve()),
    }
    if source:
        prepared["source"] = source
    return prepared


def record_export_request(prepared: dict[str, Any]) -> None:
    export_dir = Path(prepared["export_dir"])
    payload = {
        "created_at": iso_now(),
        "weights": prepared["weights"],
        "command": prepared["command"],
        "config": prepared["config"],
    }
    if "source" in prepared:
        payload["source"] = prepared["source"]
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
        source_kind=args.source_kind,
        source_id=args.source_id,
        release_root=args.release_root,
    )

    if args.dry_run:
        print(json.dumps(prepared, indent=2, sort_keys=True))
        return 0

    record_export_request(prepared)
    return run_command(prepared["command"], dry_run=False)


if __name__ == "__main__":
    raise SystemExit(main())
