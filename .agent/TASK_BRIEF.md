# TASK_BRIEF

### Task
- Bring `vision-trainer` into alignment with `docs/handoffs/WORKSPACE_NEXT_STEPS_20260430.md` by planning curated-release validation, training preparation, metadata, and export provenance support while preserving the Phase 1 bootstrap path.

### Why this update
- The workspace is adding a downstream trainer-side acceptance gate for curated releases emitted by `vision-curator`.
- `vision-trainer` currently has durable Phase 1 and Phase 2 package validators, Phase 1-only train/eval wrappers, and generic export metadata; it does not yet define or consume a curated-release contract.

### Fixed invariants (do not change)
- Direct Phase 1 package validation and smoke training remain supported as the fallback bootstrap path.
- Upstream package/release artifacts are not mutated except for existing consumer-side `.ultralytics_*` shims used by training/eval wrappers.
- Validators fail loudly on missing required metadata and do not invent provenance defaults.
- Phase 2 remains inspectable provenance/debug input, not the preferred long-term raw training contract.
- The current bootstrap target class remains `person` unless the curated release explicitly defines a compatible class list.

### Goal
- Add a repo-native curated-release acceptance and smoke-training preparation path that can be exercised against fixtures now and against a real `vision-curator` release later.

### Success criteria
- [x] A curated-release manifest contract is documented and represented by validator constants/schema artifacts.
- [x] A validator exists for curated release roots and rejects missing required metadata/layout.
- [x] Validation preserves provenance expectations for source package IDs and annotation versions.
- [x] A curated-release dry-run/preparation path can build an Ultralytics command without breaking Phase 1 `train.py` behavior.
- [x] Training/eval/export metadata can identify whether the source is a raw Phase 1 package or a curated release.
- [x] Tests cover validator success/failure cases, schema/fixture alignment, and command preparation.
- [x] Minimum verification passes: `PYTHONPATH=src python3 -m unittest discover -s tests -v` and `PYTHONPATH=src python3 -m compileall src tests`.

### Relevant files (why)
- `docs/handoffs/WORKSPACE_NEXT_STEPS_20260430.md` — source handoff for the curated-release wave.
- `docs/package_contracts.md` — durable place to define the curated-release layout next to Phase 1/Phase 2.
- `docs/training_workflow.md` — operational workflow should mention the curated-release path while retaining Phase 1 fallback.
- `docs/METRICS_AND_DIAGNOSTICS.md` — place to document curated vs gold/hard-case reporting placeholders.
- `docs/promotion_workflow.md` — place to document source curated-release metadata in export/promotion records.
- `src/bootstrap_train/validate_packages.py` — existing validation/report pattern and shared `ValidationReport` type.
- `src/bootstrap_train/train.py` — current Phase 1-only command preparation and Ultralytics dataset shim.
- `src/bootstrap_train/evaluate.py` — current Phase 1-only eval command preparation; should share provenance behavior or stay explicitly scoped.
- `src/bootstrap_train/export.py` — writes `export_request.json`; should accept/source curated-release provenance metadata.
- `src/bootstrap_train/manifests.py` — stdlib JSON/YAML helpers to reuse for release manifest parsing.
- `schemas/` — machine-readable contracts must stay aligned with validator constants.
- `configs/train/` and `configs/export/` — likely need a curated smoke config or documented metadata field.
- `tests/test_validate_packages.py` — validator fixture and failure coverage pattern.
- `tests/test_contract_artifacts.py` — schema/fixture/doc alignment coverage.
- `tests/test_workflow_commands.py` — command-preparation and export metadata coverage.
- `tests/fixtures/packages/` and `tests/fixtures/*.json` — minimal curated-release fixtures should live beside existing package fixtures.

### Refined Phase 2 Plan
1) Define the curated-release contract:
   - Add required manifest fields from the handoff: `release_id`, `source_package_ids`, `annotation_versions`, `split_policy`, `label_policy`, `class_list`, `counts_by_split`, `counts_by_label_source`, `created_at`.
   - Document expected layout: `dataset.yaml`, `splits/train.txt`, `splits/val.txt`, optional `splits/test.txt`, and provenance records when promised by the manifest.
   - Add a schema and fixture so contract docs, validator constants, and tests stay in sync.
2) Implement validation:
   - Prefer adding `validate_curated_release(root)` to `validate_packages.py` unless the module becomes too crowded; expose a CLI either via a new `validate_release.py` wrapper or an added `--release` option.
   - Validate required paths, `dataset.yaml` train/val/test references, class names, split file existence, manifest field types, counts where locally observable, and promised provenance files.
   - Return `ValidationReport(phase="curated_release", ...)` with details including `release_id`, source package IDs, annotation versions, class list, and counts.
3) Add curated-release training preparation:
   - Extend `train.py` with an explicit source type such as `--dataset-kind phase1|curated_release` or config equivalent, defaulting to Phase 1 for compatibility.
   - Reuse the existing Ultralytics dataset materialization but avoid mutating upstream release artifacts beyond the current `.ultralytics_*` consumer shim behavior.
   - Include source kind and release provenance in the returned dry-run metadata.
4) Keep eval/reporting metadata honest:
   - Decide whether `evaluate.py` should accept the same source-kind flag in this wave or explicitly remain Phase 1-only with docs noting the gap.
   - Add metadata placeholders for curated pseudo-label training set, gold validation set, and hard-case test set only as labels/provenance fields unless real curated data exists.
5) Add export provenance:
   - Extend `export.py` with optional source dataset/release metadata inputs, or consume metadata from config, so `export_request.json` can name `release_id` and source kind.
   - Preserve existing export defaults and tests.
6) Update stable docs:
   - Update only durable docs that reflect implemented behavior: package contract, training workflow, metrics/diagnostics, promotion workflow, and possibly module map/project state if entrypoints change.

### Small change sets (execution order)
1) Contract + fixtures:
   - Touch docs, schema, curated-release fixture package, and contract-artifact tests.
2) Validator + CLI:
   - Touch `validate_packages.py` and/or new `validate_release.py`, plus validator unit tests.
3) Training command path:
   - Touch `train.py`, any curated smoke config, and workflow command tests.
4) Metadata/export path:
   - Touch `evaluate.py` only if needed, `export.py`, export config/docs, and tests.
5) Durable docs:
   - Update workflow docs after behavior is verified.

### Verification
- Fast: `PYTHONPATH=src python3 -m unittest tests.test_validate_packages tests.test_workflow_commands tests.test_contract_artifacts -v`
- Targeted validator: `PYTHONPATH=src python3 -m bootstrap_train.validate_packages --release tests/fixtures/packages/curated_release_minimal`
- Targeted dry run: `PYTHONPATH=src python3 -m bootstrap_train.train --config <curated-release-config> --dataset-root tests/fixtures/packages/curated_release_minimal --dataset-kind curated_release --dry-run`
- Full: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- Compile: `PYTHONPATH=src python3 -m compileall src tests`

### Risks / gotchas
- The real `vision-curator` release schema is not locked yet; keep this contract minimal and be ready to revise names after the curator emits a real release.
- Existing `train.py` derives dataset root from `config["data"]` by taking the parent of a data file; this may be brittle for release roots and should be tested explicitly.
- Existing dataset materialization writes `.ultralytics_dataset.yaml` and `.ultralytics_splits/` inside the dataset root; this is accepted for Phase 1 but should be called out as a consumer shim for curated releases too.
- Gold validation and hard-case metrics are blocked on human-labeled data; this wave should avoid claiming evaluation quality from placeholder metadata.

### Decision rule for defaults
- Keep Phase 1 as the default path for existing configs and CLIs.
- Require an explicit source kind or curated-release-specific entrypoint/config for release validation/training so accidental Phase 1 validation is not applied to curated releases.
- Prefer metadata-first placeholders over fabricated metrics until real curator/CVAT outputs exist.

### Deferred work note
- Do not run a real end-to-end curated-release smoke train until `vision-curator` emits a release.
- Do not lock gold/hard-case evaluation claims until CVAT-labeled or otherwise curated human-reviewed data is available.
- Do not implement Xavier deployment or curator-side trust scoring in this repo.

### Phase 2 completion notes
- Added curated-release validator support to `bootstrap_train.validate_packages --release`.
- Added `dataset_kind` support for train/eval command preparation; Phase 1 remains the default.
- Added `configs/train/curated_release_smoke.yaml`.
- Added export metadata support for curated release roots via `--release-root`.
- Added curated-release schema, minimal fixture, package fixture, and tests.
- Updated package, training, metrics, and promotion workflow docs for the implemented behavior.

### Verification run
- `PYTHONPATH=src python3 -m unittest tests.test_contract_artifacts -v` — passed.
- `PYTHONPATH=src python3 -m unittest tests.test_validate_packages -v` — passed.
- `PYTHONPATH=src python3 -m bootstrap_train.validate_packages --release tests/fixtures/packages/curated_release_minimal` — passed.
- `PYTHONPATH=src python3 -m unittest tests.test_workflow_commands -v` — passed.
- `PYTHONPATH=src python3 -m bootstrap_train.train --config configs/train/curated_release_smoke.yaml --dataset-root tests/fixtures/packages/curated_release_minimal --dataset-kind curated_release --dry-run` — passed.
- `PYTHONPATH=src python3 -m bootstrap_train.export --config configs/export/onnx_fp32.yaml --weights runs/train/sample/weights/best.pt --name unit_test_export --release-root tests/fixtures/packages/curated_release_minimal --dry-run` — passed.
- `PYTHONPATH=src python3 -m unittest discover -s tests -v` — passed, 21 tests.
- `PYTHONPATH=src python3 -m compileall src tests` — passed.
