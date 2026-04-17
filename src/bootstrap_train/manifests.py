from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?\d+\.\d+$")


def iso_now() -> str:
    """Return an ISO-8601 UTC timestamp."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: str | Path) -> Any:
    """Load a JSON document from disk."""

    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: str | Path, payload: Any) -> None:
    """Write a JSON document with stable formatting."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def parse_scalar(token: str) -> Any:
    """Parse a scalar used in the repo's small YAML files."""

    text = token.strip()
    if not text:
        return ""

    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]

    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    if _INT_RE.match(text):
        return int(text)
    if _FLOAT_RE.match(text):
        return float(text)
    return text


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse a small subset of YAML mappings used by repo configs and dataset.yaml."""

    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if ":" not in stripped:
            raise ValueError(f"line {line_number}: expected 'key: value' syntax")

        key_token, value_token = stripped.split(":", 1)
        key = parse_scalar(key_token)

        while indent <= stack[-1][0]:
            stack.pop()
        current = stack[-1][1]

        value_text = value_token.strip()
        if not value_text:
            nested: dict[str, Any] = {}
            current[key] = nested
            stack.append((indent, nested))
            continue

        current[key] = parse_scalar(value_text)

    return root


def load_simple_yaml(path: str | Path) -> dict[str, Any]:
    """Load a small mapping-only YAML document from disk."""

    return parse_simple_yaml(Path(path).read_text(encoding="utf-8"))


def ensure_mapping(value: Any, context: str) -> dict[str, Any]:
    """Ensure a manifest fragment is a mapping."""

    if not isinstance(value, dict):
        raise ValueError(f"{context} must be a mapping")
    return value


def ensure_required_fields(mapping: dict[str, Any], fields: list[str], context: str) -> list[str]:
    """Return missing-field errors for the given mapping."""

    missing: list[str] = []
    for field in fields:
        if field not in mapping:
            missing.append(f"{context}: missing field '{field}'")
    return missing
