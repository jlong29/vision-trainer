# Closeout — Align Curated Release

## Decisions Made
- Added a first-class curated-release contract alongside the existing Phase 1 and Phase 2 validators instead of overloading Phase 1 assumptions.
- Kept Phase 1 as the default bootstrap path while requiring explicit curated-release selection for validation and training flows.
- Reused the existing Ultralytics materialization shim for curated releases rather than mutating upstream release artifacts.
- Extended training, evaluation, and export metadata so downstream artifacts can identify curated-release provenance honestly.

## Invariants / Gotchas
- Phase 1 remains the fallback bootstrap training path and was kept green.
- Curated-release smoke validation currently proves wiring and contract consistency, not gold-label quality.
- Consumer-side `.ultralytics_*` files remain local shims, not upstream contract changes.
- Real curated-training quality claims remain blocked on human-labeled data flowing back through `vision-curator`.

## New / Changed Commands
- `PYTHONPATH=src python3 -m bootstrap_train.validate_packages --release /path/to/curated_release`
- `PYTHONPATH=src python3 -m bootstrap_train.train --config configs/train/curated_release_smoke.yaml --dataset-root /path/to/curated_release --dataset-kind curated_release --dry-run`
- `PYTHONPATH=src python3 -m bootstrap_train.evaluate --config configs/train/phase1_eval.yaml --dataset-root /path/to/curated_release --dataset-kind curated_release --weights /path/to/best.pt`
- `PYTHONPATH=src python3 -m bootstrap_train.export --config configs/export/onnx_fp32.yaml --weights /path/to/best.pt --release-root /path/to/curated_release`

## Verification Evidence
- `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 21 tests passed.
- `PYTHONPATH=src python3 -m compileall src tests` — passed.
- `PYTHONPATH=src python3 -m bootstrap_train.validate_packages --release tests/fixtures/packages/curated_release_minimal` — passed.
- `PYTHONPATH=src python3 -m bootstrap_train.train --config configs/train/curated_release_smoke.yaml --dataset-root tests/fixtures/packages/curated_release_minimal --dataset-kind curated_release --dry-run` — passed.
- `PYTHONPATH=src python3 -m bootstrap_train.evaluate --config configs/train/phase1_eval.yaml --dataset-root tests/fixtures/packages/curated_release_minimal --dataset-kind curated_release --weights runs/train/sample/weights/best.pt --dry-run` — passed.
- `PYTHONPATH=src python3 -m bootstrap_train.export --config configs/export/onnx_fp32.yaml --weights runs/train/sample/weights/best.pt --release-root tests/fixtures/packages/curated_release_minimal --dry-run` — covered by tests and command-preparation validation.

## TODOs / Follow-Ups
- Validate against a real curated release emitted by `vision-curator`, not just the minimal fixture.
- Run a true curated-release smoke train once a real release exists.
- Keep gold-validation and hard-case reporting separate until CVAT-labeled data exists.
