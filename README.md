# vision-trainer

Desktop-side training and curation repo for thermal person detection bootstrap work.

This repo consumes handoff packages produced upstream on the Xavier NX, validates the package contracts, ingests the training-ready phase 1 dataset, inspects the provenance-rich phase 2 video package, launches Ultralytics YOLO workflows, and records export/promotion metadata for later deployment testing.

## Current scope

- Validate the Ubuntu desktop training environment.
- Validate and ingest phase 1 Ultralytics-style image packages.
- Inspect phase 2 clip packages for provenance/debug workflows.
- Launch config-driven train/eval/export commands.
- Preserve manifest provenance throughout the workflow.

## Quick start

Validate the local environment:

```bash
scripts/validate_env.sh
```

Validate a phase 1 package:

```bash
PYTHONPATH=src python -m bootstrap_train.validate_packages --phase1 /path/to/phase1_package
```

Dry-run the first smoke training command:

```bash
PYTHONPATH=src python -m bootstrap_train.train \
  --config configs/train/phase1_smoke.yaml \
  --dataset-root /path/to/phase1_package \
  --dry-run
```

Inspect a phase 2 package:

```bash
PYTHONPATH=src python -m bootstrap_train.inspect_phase2 --source /path/to/phase2_package
```

## Design constraints

- Phase 1 trains now.
- Phase 2 explains and extends phase 1.
- Upstream Xavier runtime and packaging logic stay upstream.
- Provenance fields in manifests are part of the contract and should survive every downstream step.
