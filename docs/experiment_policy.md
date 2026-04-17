# Experiment Policy

This repo is optimized for repeatable bootstrap training, not framework sprawl.

## Output conventions

- Training runs write to `runs/train/<name>`.
- Evaluation runs write to `runs/val/<name>`.
- Export requests write metadata to `artifacts/exports/<name>/`.
- Ingested datasets land under `data/phase1_packages/<package_name>/` by default.

## Minimum run record

Each meaningful run should retain:

- the train/eval/export config used
- the dataset root and upstream `package_id`
- the Ultralytics command that was executed
- notable environment context if the run is promoted or compared

## Bootstrap defaults

- First validate on `yolo11n` or `yolo11s`.
- Run single-GPU smoke before multi-GPU.
- Preserve manifest provenance instead of flattening package metadata into ad hoc notes.

## Non-goals for v1

- No CVAT integration unless explicitly requested
- No temporal model training unless explicitly requested
- No duplication of Xavier runtime code
- No broad support for many model families in the first iteration
