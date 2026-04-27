from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from bootstrap_train.validate_packages import (
    PHASE1_ENTRY_FIELDS,
    PHASE1_SOURCE_FIELDS,
    PHASE1_TOP_LEVEL_FIELDS,
    PHASE2_CLIP_FIELDS,
    PHASE2_SOURCE_FIELDS,
    PHASE2_TOP_LEVEL_FIELDS,
)


def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _resolve_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise AssertionError(f"unsupported ref: {ref}")

    node: Any = root_schema
    for part in ref[2:].split("/"):
        node = node[part]
    if not isinstance(node, dict):
        raise AssertionError(f"resolved ref is not a schema object: {ref}")
    return node


def _assert_matches_schema(schema: dict[str, Any], payload: Any, root_schema: dict[str, Any]) -> None:
    if "$ref" in schema:
        _assert_matches_schema(_resolve_ref(root_schema, schema["$ref"]), payload, root_schema)
        return

    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(payload, dict):
            raise AssertionError(f"expected object, got {type(payload).__name__}")
        for field in schema.get("required", []):
            if field not in payload:
                raise AssertionError(f"missing required field: {field}")
        for key, value in payload.items():
            properties = schema.get("properties", {})
            if key in properties:
                _assert_matches_schema(properties[key], value, root_schema)
        return

    if schema_type == "array":
        if not isinstance(payload, list):
            raise AssertionError(f"expected array, got {type(payload).__name__}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for item in payload:
                _assert_matches_schema(item_schema, item, root_schema)
        return

    if schema_type == "string":
        if not isinstance(payload, str):
            raise AssertionError(f"expected string, got {type(payload).__name__}")
        return

    if schema_type == "integer":
        if isinstance(payload, bool) or not isinstance(payload, int):
            raise AssertionError(f"expected integer, got {type(payload).__name__}")
        return

    if schema_type == "number":
        if isinstance(payload, bool) or not isinstance(payload, (int, float)):
            raise AssertionError(f"expected number, got {type(payload).__name__}")
        return

    if schema_type == "boolean":
        if not isinstance(payload, bool):
            raise AssertionError(f"expected boolean, got {type(payload).__name__}")
        return


class ContractArtifactsTest(unittest.TestCase):
    def test_phase1_schema_matches_validator_constants(self) -> None:
        schema = _load_json("schemas/phase1_manifest.schema.json")
        self.assertEqual(schema["required"], PHASE1_TOP_LEVEL_FIELDS)
        self.assertEqual(schema["$defs"]["source"]["required"], PHASE1_SOURCE_FIELDS)
        self.assertEqual(schema["$defs"]["entry"]["required"], PHASE1_ENTRY_FIELDS)

    def test_phase2_schema_matches_validator_constants(self) -> None:
        schema = _load_json("schemas/phase2_manifest.schema.json")
        self.assertEqual(schema["required"], PHASE2_TOP_LEVEL_FIELDS)
        self.assertEqual(schema["$defs"]["source"]["required"], PHASE2_SOURCE_FIELDS)
        self.assertEqual(schema["$defs"]["clip"]["required"], PHASE2_CLIP_FIELDS)

    def test_phase1_fixture_matches_schema(self) -> None:
        schema = _load_json("schemas/phase1_manifest.schema.json")
        fixture = _load_json("tests/fixtures/phase1_manifest_minimal.json")
        _assert_matches_schema(schema, fixture, schema)

    def test_phase2_fixture_matches_schema(self) -> None:
        schema = _load_json("schemas/phase2_manifest.schema.json")
        fixture = _load_json("tests/fixtures/phase2_manifest_minimal.json")
        _assert_matches_schema(schema, fixture, schema)

    def test_handoff_docs_exist(self) -> None:
        for path in [
            "docs/handoffs/README.md",
            "docs/handoffs/EDGE_TO_DESKTOP.md",
            "docs/handoffs/DESKTOP_TO_EDGE.md",
        ]:
            self.assertTrue(Path(path).exists(), path)


if __name__ == "__main__":
    unittest.main()
