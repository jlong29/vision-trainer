# Module Map

## `src/bootstrap_train/`

- `manifests.py` parses JSON and simple YAML mappings used by package manifests and configs.
- `validate_packages.py` validates phase 1 and phase 2 package contracts and emits structured summaries.
- `ingest_phase1.py` copies validated phase 1 packages into repo-controlled storage and records the ingest.
- `inspect_phase2.py` summarizes phase 2 package structure for review/debug workflows.
- `train.py` builds and optionally executes config-driven `yolo ... train` commands.
- `evaluate.py` builds and optionally executes config-driven `yolo ... val` commands.
- `export.py` builds and optionally executes config-driven `yolo ... export` commands and records export metadata.

## Supporting dirs

- `configs/` contains operator-facing defaults.
- `docs/handoffs/` contains tracked edge/desktop coordination notes.
- `schemas/` contains machine-readable manifest contracts.
- `scripts/` contains shell wrappers for common validation/bootstrap flows.
- `tests/` contains stdlib-based regression coverage for validators and dry-run command construction.
