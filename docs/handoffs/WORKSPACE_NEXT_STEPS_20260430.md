# Workspace Next Steps — `vision-trainer`

## Context
This packet is the desktop-side `vision-trainer` execution slice for the workspace root task **Bootstrap vision next wave across edge, curator, and trainer**.

Read first:
- `AGENTS.md`
- `docs/package_contracts.md`
- `docs/training_workflow.md`
- `docs/METRICS_AND_DIAGNOSTICS.md`
- `docs/promotion_workflow.md`
- workspace: `docs/SYSTEM_DESIGN_v1.md`
- workspace: `docs/PROPOSED_PLAN_v1.md`

## Mission for this wave
Keep the current Phase 1 smoke-training path intact, but add the first trainer-side support for curated releases coming from `vision-curator`.

Do not reimplement curator logic here. Do not become the preferred raw Phase 2 parser for long-term use. Preserve direct Phase 1 bootstrap training as a fallback path.

## What the other nodes are doing in parallel
The Xavier NX node is updating runtime and package provenance in `vision_api` and `thermal-data-engine`.
The `vision-curator` agent is expected to harden ingest, trust scoring, review queues, and a first draft curated release contract.

Your job is to create the downstream acceptance gate and smoke-train preparation path.

## Concrete objectives

### Objective 1, define and validate the curated-release contract
Acceptance:
- A validator exists for curated release manifests.
- Validation fails loudly on missing required metadata.
- Validation preserves provenance expectations back to source packages and annotation versions.

Recommended minimum required manifest fields:
- `release_id`
- `source_package_ids`
- `annotation_versions`
- `split_policy`
- `label_policy`
- `class_list`
- `counts_by_split`
- `counts_by_label_source`
- `created_at`

Also validate the expected file layout:
- `dataset.yaml`
- `splits/train.txt`
- `splits/val.txt`
- optional `splits/test.txt`
- provenance records if the release promises them

### Objective 2, add a curated-release consumer path without breaking Phase 1
Acceptance:
- The repo can dry-run or prepare a training command from a curated release root.
- Existing Phase 1 package validation and smoke training still work.
- The curated-release path does not mutate upstream release artifacts.

A reasonable implementation is:
- add a `validate_release.py` or expand the existing validator module
- add a training wrapper that can read a release root, verify its dataset files, and then launch the same Ultralytics flow

### Objective 3, keep evaluation reporting honest
Acceptance:
- Training/eval metadata distinguishes curated release provenance from raw Phase 1 bootstrap provenance.
- If possible this wave, add placeholders for reporting separate metrics on:
  - curated pseudo-label training set
  - gold validation set
  - hard-case test set

This can be metadata-first before it is fully populated with real data.

### Objective 4, prepare for downstream model promotion without implementing it fully here
Acceptance:
- Export or artifact metadata can name the source curated release.
- The repo has a clear place to record that a candidate model came from curated release X, not just an unnamed smoke run.

## Human-in-the-loop gates
These are real dependencies.

### Gate A, wait for a curator release
You can build validators and wrappers now, but a true end-to-end curated-release smoke run needs a release emitted by `vision-curator`.

### Gate B, wait for CVAT-labeled or otherwise curated data
A pseudo-only smoke release is acceptable for early wiring. Hard-case and gold-negative evaluation become meaningful only after Dr. Long labels data in CVAT and that annotation is imported back into `vision-curator`.

## Parallelism guidance
Can run now, in parallel with NX and curator work:
- release validator implementation
- training-wrapper support for curated releases
- metadata/reporting updates for curated provenance

Should wait for curator output:
- final schema lock
- end-to-end dry run against a real curated release

Should wait for human labeling:
- any claim of gold validation, gold negatives, or frozen hard-case evaluation quality

## Verification
Minimum:
```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m compileall src tests
```

Targeted after adding a release validator:
```bash
PYTHONPATH=src python3 -m bootstrap_train.validate_release --release /path/to/release
```

Targeted after adding a curated-release dry run:
```bash
PYTHONPATH=src python3 -m bootstrap_train.train --config <curated-release-config> --dataset-root /path/to/release --dry-run
```

## Definition of done for this wave
This packet is complete when:
- the repo validates curated releases explicitly,
- a curated-release training preparation path exists,
- Phase 1 bootstrap support still passes,
- output metadata can identify the source curated release,
- the handoff back to workspace states exactly what remains blocked on curator output or human labeling.

## Deliver back to workspace
Report:
- files changed
- commands run
- whether the repo validated only fixtures or a real curated release
- whether Phase 1 direct training support remained green
- any schema mismatches you had to push back to `vision-curator`
