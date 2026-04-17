from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from .manifests import dump_json, iso_now, load_json
from .validate_packages import validate_phase1_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Copy a validated phase 1 package into repo-controlled storage.")
    parser.add_argument("--source", required=True, help="Path to the upstream phase 1 package root.")
    parser.add_argument("--dest-root", required=True, help="Directory that will contain copied phase 1 packages.")
    parser.add_argument("--name", help="Override the destination package directory name.")
    return parser


def _package_name(source: Path, override: str | None) -> str:
    if override:
        return override
    manifest = load_json(source / "manifest.json")
    if isinstance(manifest, dict) and manifest.get("package_id"):
        return str(manifest["package_id"])
    return source.name


def ingest_phase1_package(source: str | Path, dest_root: str | Path, name: str | None = None) -> dict[str, Any]:
    source_root = Path(source)
    report = validate_phase1_package(source_root)
    if not report.ok:
        raise ValueError("phase 1 package is invalid; run validate_packages.py for details")

    target_root = Path(dest_root)
    target_root.mkdir(parents=True, exist_ok=True)
    package_name = _package_name(source_root, name)
    destination = target_root / package_name
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")

    shutil.copytree(source_root, destination)

    receipt = {
        "ingested_at": iso_now(),
        "source_root": str(source_root.resolve()),
        "destination_root": str(destination.resolve()),
        "package_name": package_name,
        "package_id": report.details.get("package_id"),
        "validation": report.to_dict(),
    }
    dump_json(target_root / "ingest_receipts" / f"{package_name}.json", receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    receipt = ingest_phase1_package(args.source, args.dest_root, name=args.name)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
