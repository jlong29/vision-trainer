from __future__ import annotations

import argparse
import json

from .validate_packages import validate_phase2_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect a phase 2 provenance package.")
    parser.add_argument("--source", required=True, help="Path to the phase 2 package root.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = validate_phase2_package(args.source)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
