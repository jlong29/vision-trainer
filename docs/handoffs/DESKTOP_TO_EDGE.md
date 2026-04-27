# Desktop To Edge

## 2026-04-27

### Author / node
- desktop

### Summary
- Phase 1 and Phase 2 smoke validation passed on the desktop host.
- Single-GPU and 3-GPU Phase 1 smoke training passed through the repo wrapper after consumer-side Ultralytics path normalization fixes.

### Evidence
- Desktop wrappers: `src/bootstrap_train/train.py`, `src/bootstrap_train/evaluate.py`
- Contract docs: `docs/package_contracts.md`
- Archived closeout: `docs/codex/tasks/20260427_1630_bootstrap_smoke_validation/CLOSEOUT.md`

### Requested action
- Continue producing the current Phase 1 and Phase 2 package contracts without format changes unless a future contract-change task is opened jointly.

### Contract impact
- clarification

### Notes
- The earlier smoke-train failure was caused by desktop-side Ultralytics path resolution, not corrupted edge package contents.
- The desktop consumer now materializes temporary `.ultralytics_*` files with absolute paths while preserving the upstream handoff package unchanged.
