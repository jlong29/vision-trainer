# Schemas

This directory contains machine-readable contract artifacts for upstream package manifests consumed by `vision-trainer`.

## Current scope

- `phase1_manifest.schema.json` — schema for the Phase 1 `manifest.json`
- `phase2_manifest.schema.json` — schema for the Phase 2 `manifest.json`
- `curated_release_manifest.schema.json` — schema for a curator-emitted release `manifest.json`

## Update rules

- Update schemas in the same task as any contract change.
- Keep `src/bootstrap_train/validate_packages.py` and `tests/test_contract_artifacts.py` in sync with the schema files.
- If a schema changes, update the matching human-readable documentation in `docs/package_contracts.md` and summarize the change in `docs/handoffs/`.
