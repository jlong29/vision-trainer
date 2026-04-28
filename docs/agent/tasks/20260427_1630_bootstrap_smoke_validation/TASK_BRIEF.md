## TASK_BRIEF

### Task
- Bootstrap `vision-trainer` from `YOLO.md` by converting the generic agent template into a repo-specific `AGENTS.md`, creating `.agent/` scratch files, and scaffolding the initial desktop training/validation repo.

### Why this update
- The repository currently contains only the design handoff and agent template, but the desktop training repo needs concrete code, configs, docs, and bootstrap scripts that match the validated Xavier package contracts.

### Fixed invariants (do not change)
- Preserve the phase 1 and phase 2 package contracts described in `YOLO.md`.
- Keep phase 1 as the initial direct training input and phase 2 as inspection/provenance input.
- Do not duplicate Xavier runtime or packaging logic in this repo.

### Goal
- Create a usable v1 bootstrap repo that can validate environment/package inputs, launch training/evaluation/export commands, and document the workflow clearly.

### Success criteria
- [x] `AGENTS.md` is repo-specific and reflects the `YOLO.md` design constraints.
- [x] `.agent/` exists with task and memory scratch files.
- [x] The repo contains the initial scaffold under `src/`, `configs/`, `docs/`, `scripts/`, and `tests/`.
- [x] The bootstrap code passes local lightweight verification.

### Relevant files (why)
- `YOLO.md` — source design doc for package contracts, workflow, and repo scope
- `AGENTS.md` — always-on repo-specific agent instructions
- `src/bootstrap_train/validate_packages.py` — contract enforcement for phase 1 and phase 2 inputs
- `src/bootstrap_train/train.py` — config-driven training launcher
- `tests/` — regression coverage for the bootstrap logic

### Refined Phase 2 Plan
1) Convert the agent template into repo-specific operating instructions and create `.agent/` scratch artifacts.
2) Scaffold the Python package, configs, docs, and helper scripts around the desktop bootstrap workflow.
3) Add tests for validators and dry-run command builders, then run lightweight verification.

### Small change sets (execution order)
1) Agent/bootstrap metadata: `AGENTS.md`, `.gitignore`, `.agent/`
2) Repo skeleton and docs: `README.md`, `pyproject.toml`, `configs/`, `docs/`
3) Runtime code and tests: `src/bootstrap_train/`, `scripts/`, `tests/`

### Verification
- Fast: `PYTHONPATH=src python -m unittest discover -s tests -v`
- Targeted: `PYTHONPATH=src python -m compileall src tests`
- Full: `PYTHONPATH=src python -m bootstrap_train.train --config configs/train/phase1_smoke.yaml --dataset-root /path/to/phase1_package --dry-run`

### Risks / gotchas
- Ultralytics and PyTorch are not installed in this workspace, so the implementation must bootstrap without importing them at module import time.
- YAML parsing must work for repo configs and `dataset.yaml` without forcing third-party dependencies.

### Decision rule for defaults
- Use conservative defaults that match the design doc: single-GPU smoke first, then multi-GPU with explicit `device=0,1,2`.

### Deferred work note
- Real Ultralytics training runs, experiment comparison dashboards, and Xavier deployment promotion remain follow-on tasks after the bootstrap scaffold is in place.
