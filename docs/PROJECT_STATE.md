# Project State

## Current status

As of April 17, 2026, `vision-trainer` is in bootstrap mode.

- The Xavier NX edge workflow is assumed to be upstream and already validated.
- The desktop environment has already installed PyTorch and Ultralytics in the `yolo11` environment.
- This repo now owns desktop-side validation, ingest, training orchestration, evaluation orchestration, and export stubs.

## Immediate next actions

- Validate a real phase 1 package with the local validator.
- Run the single-GPU smoke train.
- Run the 3-GPU smoke train.
- Review output organization and extend experiment comparison/reporting as needed.
