## TASK_BRIEF

### Task
- Add tracked repo infrastructure for desktop-to-edge and edge-to-desktop communication, including durable handoff docs, manifest schemas, and contract regression checks.

### Why this update
- The bootstrap repo and smoke tests are now working, and the next coordination problem is durable cross-node communication that survives beyond ephemeral `.agent/` scratch state.

### Fixed invariants (do not change)
- Keep `.agent/` scratch-only and untracked.
- Preserve the existing Phase 1 and Phase 2 upstream package contracts unless an explicit contract-change task is approved.
- Keep the edge node as the producer and this repo as the desktop consumer/curator.

### Goal
- Make this repository the durable communication channel between the Xavier edge node and the desktop training node without relying on ad hoc chat-only state.

### Success criteria
- [x] Add tracked handoff docs under a stable repo location such as `docs/handoffs/`.
- [x] Add machine-readable schema or contract artifacts for Phase 1 and Phase 2 manifests.
- [x] Add regression tests or CI checks that fail on contract drift.
- [x] Document the workflow for how edge and desktop agents should exchange status and contract updates through the repo.

### Relevant files (why)
- `docs/package_contracts.md` — current human-readable contract source
- `src/bootstrap_train/validate_packages.py` — current executable contract enforcement
- `tests/` — place to extend contract regression coverage
- `docs/PROJECT_STATE.md` — durable workflow/state summary
- `AGENTS.md` — durable agent operating guidance

### Refined Phase 2 Plan
1) Define the tracked communication surface: handoff docs, schemas, and test hooks.
2) Implement the initial tracked artifacts and validation coverage.
3) Update repo docs so both edge and desktop agents follow the same communication workflow.

### Small change sets (execution order)
1) Communication docs: `docs/handoffs/`, `docs/PROJECT_STATE.md`, `AGENTS.md`
2) Contract artifacts: `schemas/` or equivalent tracked schema location
3) Regression enforcement: `tests/` and CI/config hooks if present

### Verification
- Fast: `PYTHONPATH=src python -m unittest discover -s tests -v`
- Targeted: `PYTHONPATH=src python -m unittest tests.test_contract_artifacts -v`
- Full: `.github/workflows/contracts.yml`

### Risks / gotchas
- Human-readable docs without executable checks will drift quickly.
- Over-designing the communication layer too early will slow down actual model work.

### Decision rule for defaults
- Prefer the smallest tracked structure that gives both agents a single durable place for status, contracts, and validation outcomes.

### Deferred work note
- Do not expand into deployment orchestration or temporal-model workflow changes in this task unless explicitly requested.
