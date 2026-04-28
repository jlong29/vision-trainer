# Closeout

## Task

Bootstrap `vision-trainer` from the design handoff, validate the desktop-side Phase 1 and Phase 2 workflows, and resolve smoke-test issues through a repo-owned training wrapper.

## Decisions made

- Converted the generic template into a repo-specific `AGENTS.md` so future work starts from the actual Xavier-to-desktop workflow and package contracts.
- Kept the first implementation stdlib-first for validators and command launchers so the repo remains usable before optional training dependencies are present.
- Preserved the upstream Phase 1 and Phase 2 contracts and fixed Ultralytics path quirks in consumer-side wrapper shims instead of changing the edge producer format.
- Adopted the repo wrapper as the preferred training/eval interface because it generates temporary `.ultralytics_*` path-normalization files safely inside the package root.

## New invariants and gotchas

- Phase 1 and Phase 2 real smoke validation passed on the desktop host; the edge-produced packages are structurally sound for the current consumer workflow.
- Ultralytics `8.4.38` on the desktop host mis-resolved both `dataset.yaml path` and split-file image paths when relative paths were used.
- `bootstrap_train.train` and `bootstrap_train.evaluate` now materialize `.ultralytics_dataset.yaml` plus `.ultralytics_splits/*.txt` with absolute paths as consumer-side shims.
- These `.ultralytics_*` files are runtime convenience artifacts only; they do not change the upstream package contract.

## New or changed commands

- Validate a Phase 1 package:
  - `PYTHONPATH=src python -m bootstrap_train.validate_packages --phase1 <phase1_root>`
- Inspect a Phase 2 package:
  - `PYTHONPATH=src python -m bootstrap_train.inspect_phase2 --source <phase2_root>`
- Preferred single-GPU smoke train:
  - `PYTHONPATH=src python -m bootstrap_train.train --config configs/train/phase1_smoke.yaml --dataset-root <phase1_root>`
- Preferred 3-GPU smoke train:
  - `PYTHONPATH=src python -m bootstrap_train.train --config configs/train/phase1_ddp.yaml --dataset-root <phase1_root>`

## Verification evidence

- `PYTHONPATH=src python -m unittest discover -s tests -v`
  - Passed with 6 tests.
- `PYTHONPATH=src python -m compileall src tests`
  - Passed.
- Synthetic dry run of `bootstrap_train.train`
  - Generated the expected `yolo detect train ...` command plus normalized `.ultralytics_*` files.
- Real host smoke runs reported by user:
  - Phase 1 validation passed.
  - Phase 2 validation/inspection passed.
  - Single-GPU smoke training passed after wrapper normalization fixes.
  - 3-GPU smoke training passed after wrapper normalization fixes.

## Follow-ups

- Add tracked repo infrastructure for edge/desktop communication.
- Add manifest schemas and contract regression checks shared across producer and consumer workflows.
- Expand experiment comparison and promotion workflow once handoff infrastructure is in place.
