# Project State

## Current status

As of April 17, 2026, `vision-trainer` is in bootstrap mode.

- The Xavier NX edge workflow is assumed to be upstream and already validated.
- The desktop environment has already installed PyTorch and Ultralytics in the `yolo11` environment.
- This repo now owns desktop-side validation, ingest, training orchestration, evaluation orchestration, and export stubs.
- Phase 1 and Phase 2 package smoke validation passed against real handoff packages on the desktop host.
- Single-GPU and 3-GPU smoke training now work through the repo wrapper after normalizing Ultralytics dataset and split paths at runtime.
- Tracked edge/desktop handoff notes and manifest schemas now live in-repo instead of relying only on `.agent/` scratch state.

## Immediate next actions

- Start using `docs/handoffs/EDGE_TO_DESKTOP.md` and `docs/handoffs/DESKTOP_TO_EDGE.md` as the durable coordination surface for both nodes.
- Extend schema coverage if the upstream manifest contracts grow beyond the current required fields.
- Review output organization and extend experiment comparison/reporting as needed.
