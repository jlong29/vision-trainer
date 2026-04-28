# .agent/MEMORY.md (scratch)

**Task:** contract-acceptance-checks  
**Last updated:** 2026-04-27 20:28 EDT

## Goal / status
- Implementation and verification complete.
- Added tiny Phase 1 / Phase 2 package-directory fixtures under `tests/fixtures/packages/`.
- Added validator-backed acceptance coverage in `tests/test_validate_packages.py` and fixture-layout contract checks in `tests/test_contract_artifacts.py`.
- Branch in use: `feature/contract-acceptance-checks`.

## Repro commands
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- `PYTHONPATH=src python -m unittest tests.test_contract_artifacts tests.test_validate_packages -v`
- `PYTHONPATH=src python -m compileall src tests`

## Hypotheses + evidence
- A tiny package-directory fixture per phase will give better producer/consumer acceptance coverage than manifest-only fixtures.
  - Evidence: current repo already validates schemas/constants and temp-built directories, but does not keep one durable package fixture that mirrors the real edge output layout.

## Decisions (and why)
- Keep the acceptance authority in `vision-trainer`, because compatibility matters most at the consumer.
- Keep the fixtures tiny and structural.

## Next steps
- Commit and push the tracked `vision-trainer` changes.
- Decide whether to do repo-local closeout immediately or keep the task open for follow-on refinement.
