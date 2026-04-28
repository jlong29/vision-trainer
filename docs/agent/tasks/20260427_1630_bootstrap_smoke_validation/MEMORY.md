# .agent/MEMORY.md (scratch)

**Task:** bootstrap_vision_trainer  
**Last updated:** 2026-04-27 16:30

## Goal / status
- Bootstrap the desktop training repo from the design doc.
- Completed: repo-specific agent instructions, bootstrap scaffold, docs/configs, scripts, and tests are in place.
- Target desktop environment already has the validated `yolo11` conda env, PyTorch 2.6.0, and Ultralytics installed.
- Real desktop smoke validation passed for both the Phase 1 and Phase 2 handoff packages.
- Real single-GPU and 3-GPU smoke training passed after fixing Ultralytics path normalization on the desktop consumer side.

## Repro commands
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- `PYTHONPATH=src python -m compileall src tests`

## Hypotheses + evidence
- The repo can stay stdlib-first for validators and command launchers, which avoids blocking on `ultralytics` during bootstrap.
- The design doc is explicit enough to define phase 1 and phase 2 validators without inspecting upstream code.

## Decisions (and why)
- Keep the first implementation focused on validation, command orchestration, and documentation rather than embedded training framework logic.
- Preserve `.agent/` as ignored scratch so later tasks can reuse it without polluting git history.
- Treat the installed target environment as the operational default, but keep Python modules import-safe without Ultralytics for bootstrap verification and fresh checkouts.
- Keep the upstream Phase 1 package contract unchanged and solve Ultralytics path quirks in consumer-side wrapper shims instead of asking the edge producer to mutate its handoff format.

## Gotchas discovered (promote at closeout)
- `docs/codex` is already ignored in the initial repo state.
- The repo started with only design docs, so every durable entrypoint needs to be created from scratch.
- Ultralytics 8.4.38 on the desktop host mis-resolved `dataset.yaml path` and split-file image paths unless the wrapper materialized absolute-path `.ultralytics_*` shims.

## Verification run
- Command(s): `PYTHONPATH=src python -m unittest discover -s tests -v`
- Outcome(s): 6 tests passed.
- Command(s): `PYTHONPATH=src python -m compileall src tests`
- Outcome(s): compile pass succeeded.
- Command(s): `PYTHONPATH=src python -m bootstrap_train.train --config configs/train/phase1_smoke.yaml --dataset-root <synthetic_phase1_root> --dry-run`
- Outcome(s): dry-run produced the expected `yolo detect train ...` command with validated dataset metadata.
- Command(s): `PYTHONPATH=src python -m bootstrap_train.validate_packages --phase1 <real_phase1_root>` and `PYTHONPATH=src python -m bootstrap_train.inspect_phase2 --source <real_phase2_root>`
- Outcome(s): both real package smoke validations passed on the desktop host.
- Command(s): `PYTHONPATH=src python -m bootstrap_train.train --config configs/train/phase1_smoke.yaml --dataset-root <real_phase1_root>` and `PYTHONPATH=src python -m bootstrap_train.train --config configs/train/phase1_ddp.yaml --dataset-root <real_phase1_root>`
- Outcome(s): single-GPU and 3-GPU smoke training passed after wrapper normalization fixes.

## Next steps
- Add tracked handoff infrastructure for edge/desktop communication inside the repo.
- Add manifest schema artifacts and contract regression checks shared across edge and desktop consumers.
