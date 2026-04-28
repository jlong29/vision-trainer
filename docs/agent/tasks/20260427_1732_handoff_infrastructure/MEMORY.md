# .agent/MEMORY.md (scratch)

**Task:** edge_desktop_handoff_infrastructure  
**Last updated:** 2026-04-27 16:30

## Goal / status
- Add tracked handoff docs, machine-readable manifest schemas, and regression checks for edge/desktop communication.
- Completed: docs, schemas, fixtures, tests, and CI workflow are in place.

## Repro commands
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- `PYTHONPATH=src python -m unittest tests.test_contract_artifacts -v`
- `PYTHONPATH=src python -m compileall src tests`

## Hypotheses + evidence
- A small tracked docs surface plus schema/tests is enough to coordinate the two nodes without adding heavyweight infrastructure.
- Schema drift is best caught by tying machine-readable schemas directly to the validator constants in `src/bootstrap_train/validate_packages.py`.

## Decisions (and why)
- Keep communication durable and lightweight by using tracked Markdown under `docs/handoffs/`.
- Keep machine-readable contracts in `schemas/` and enforce drift through stdlib tests plus CI rather than introducing a new runtime dependency.

## Gotchas discovered (promote at closeout)
- Human-readable contract docs alone are too easy to drift; schema/tests need to move in the same change set as validator edits.

## Verification run
- Command(s):  
- Outcome(s):  
- Command(s): `PYTHONPATH=src python -m unittest discover -s tests -v`
- Outcome(s): 11 tests passed.
- Command(s): `PYTHONPATH=src python -m unittest tests.test_contract_artifacts -v`
- Outcome(s): 5 contract-artifact tests passed.
- Command(s): `PYTHONPATH=src python -m compileall src tests`
- Outcome(s): compile pass succeeded.

## Next steps
- Start using the handoff docs as the normal cross-node communication channel.
- Extend schema coverage if manifest semantics grow beyond the current required fields.
