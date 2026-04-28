# TASK_BRIEF

### Root-task linkage
- Seeded from workspace root task: `Producer-consumer contract acceptance checks`
- Designated active repo under `ACTIVE_TASK.md`: `src/vision-trainer`

### Task
- Add a producer/consumer contract acceptance layer in `vision-trainer` that checks real package-directory fixtures, not only isolated manifest fixtures.

### Why this update
- The current repo already has useful contract surfaces: `docs/package_contracts.md`, machine-readable schemas, validator constants, package validators, and minimal manifest fixtures.
- What is still missing is an explicit acceptance check that says: "a package shaped like the edge producer's real output is accepted end-to-end by the desktop consumer repo."
- That is the exact regression class we now care about across `thermal-data-engine` → `vision-trainer`: compatibility drift between producer output and consumer expectations.

### Fixed invariants (do not change)
- Preserve the current upstream Xavier package contracts unless this task explicitly changes them.
- Keep the acceptance authority on the desktop consumer side.
- Treat phase 1 as the current direct training contract.
- Treat phase 2 as the current inspectable temporal/provenance contract, not yet a direct Ultralytics training contract.
- Keep tests stdlib-first and runnable with `PYTHONPATH=src python -m unittest ...`.

### Goal
- Make the desktop repo fail loudly if producer/consumer compatibility drifts, using tiny package-directory fixtures that look like real edge handoff artifacts.

### Success criteria
- [x] Add tiny package-directory fixtures for phase 1 and phase 2 under `tests/fixtures/`.
- [x] Add a contract acceptance test that runs `validate_phase1_package(...)` and `validate_phase2_package(...)` against those directory fixtures.
- [x] Add a contract-artifact test that checks fixture structure against `docs/package_contracts.md` expectations at a high-signal level.
- [x] Keep schemas, validator constants, and fixture expectations aligned.
- [x] Verification passes with repo-default unittest and compileall commands (using `python3` in this environment because `python` resolves to 2.7).

### Relevant files (why)
- `docs/package_contracts.md` — human-readable contract source of truth
- `schemas/phase1_manifest.schema.json` — machine-readable phase 1 manifest contract
- `schemas/phase2_manifest.schema.json` — machine-readable phase 2 manifest contract
- `src/bootstrap_train/validate_packages.py` — consumer-side acceptance authority for package validation
- `tests/test_contract_artifacts.py` — current schema/fixture/document existence checks
- `tests/test_validate_packages.py` — current package validator coverage using temp-built package directories
- `.github/workflows/contracts.yml` — CI path that should catch contract drift automatically

### Proposed plan
1) Add two tiny fixture package directories:
   - `tests/fixtures/packages/phase1_minimal/`
   - `tests/fixtures/packages/phase2_minimal/`
2) Populate them with the minimum real layout expected from edge output:
   - phase 1: `dataset.yaml`, `images/`, `labels/`, `splits/`, `manifest.json`
   - phase 2: `manifest.json`, `clips/<package_clip_id>/clip.mp4`, `clip_manifest.json`, `detections.parquet`, `tracks.parquet`
3) Add tests that validate those fixtures through the actual consumer validator functions.
4) Extend `tests/test_contract_artifacts.py` with a small "fixture layout matches contract doc intent" check so docs/schema/validator/fixtures stay conceptually aligned.
5) Keep the existing temp-builder tests, because they still give targeted isolated coverage for validator behavior.

### Verification
- Fast: `PYTHONPATH=src python3 -m compileall src tests`
- Default: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- Focused: `PYTHONPATH=src python3 -m unittest tests.test_contract_artifacts tests.test_validate_packages -v`

### Risks / gotchas
- The fixture package directories should stay tiny and structural, not become large binary-heavy golden datasets.
- The contract acceptance check should prove consumer compatibility, not accidentally duplicate all validator logic inside tests.
- Phase 2 should not be overclaimed as trainable just because the fixture validates structurally.

### Decision rule for defaults
- Prefer one tiny "known-good accepted package" fixture per phase over many overlapping fixtures.
- Add more fixtures only when a new incompatibility class is discovered.

### Deferred work note
- Do not add a producer-side exporter test in this repo.
- Do not make this task responsible for changing the phase 1 or phase 2 contract unless the evidence says the current contract is insufficient.
- Do not redesign the edge/desktop handoff model, just strengthen acceptance checking around it.
- Repo-local closeout is still pending even though the implementation and verification boxes are now checked.
