# AGENTS.md — vision-trainer

You are an AI coding agent operating inside the `vision-trainer` repository.

This file is always-on guidance. Keep it short, stable, and high-signal. If something is task-specific, it belongs in `.agent/TASK_BRIEF.md`, `.agent/MEMORY.md`, or other `.agent/` scratch artifacts, not here.

---

## Mission
`vision-trainer` is the desktop-side training and curation repo for thermal person detection.

It consumes validated handoff packages produced upstream on the Xavier NX, validates their contracts, materializes training inputs, runs Ultralytics YOLO training/evaluation on the Ubuntu 22.04 desktop host, and prepares candidate artifacts for later Xavier deployment.

The dominant workflow is: validate environment, validate/ingest phase 1 package, run single-GPU smoke training, step up to 3-GPU training, compare outputs, and export a promotion candidate without reimplementing edge runtime code.

## Source of truth
When docs and code disagree, trust these files:
- `src/bootstrap_train/validate_packages.py`
- `src/bootstrap_train/train.py`
- `src/bootstrap_train/export.py`
- `docs/package_contracts.md`
- `configs/train/phase1_smoke.yaml`

Additional repo-specific rules:
- Preserve the upstream Xavier package contracts. Do not rewrite or silently drop provenance fields from `manifest.json` files.
- Treat phase 1 as the current direct training contract. Treat phase 2 as inspectable provenance/debug input unless an explicit converter is added.
- Optimize for reproducible desktop training on Ubuntu 22.04 / Python 3.10 with the validated 3x GTX 1080 Ti host.

---

## Repo map

### High-signal code
- `src/bootstrap_train/` — desktop training bootstrap tooling
  - `validate_packages.py` — validates phase 1 and phase 2 package contracts before downstream use
  - `ingest_phase1.py` — copies a validated phase 1 package into a repo-controlled location and records the ingest
  - `train.py` — config-driven Ultralytics training launcher with preflight validation
  - `evaluate.py` — config-driven evaluation launcher for trained weights
  - `export.py` — export/promotion stub for candidate model artifacts
  - `inspect_phase2.py` — summarizes the provenance-rich video package for review/debug use
  - `manifests.py` — shared JSON/YAML-lite parsing and manifest helpers
- `configs/` — operator-editable configs for train/data/export workflows
- `docs/` — durable package contracts, workflow guidance, handoff notes, and module/state docs
- `schemas/` — machine-readable manifest contracts that must stay aligned with the validators
- `scripts/` — shell entrypoints for environment validation and smoke workflows
- `tests/` — stdlib test coverage for validators and command builders

### Large/noisy dirs (do not scan by default)
Avoid expensive traversal unless explicitly needed:
- `data/`
- `runs/`
- `artifacts/`
- `.agent/logs/`
- `__pycache__/`

Use targeted commands instead (e.g., `ls <dir>`, `find <dir> -maxdepth 2 ...`, `rg ...`) and keep outputs small.

---

## Core workflow (minimal commands)

### Build / prepare / ingest
```bash
scripts/validate_env.sh
PYTHONPATH=src python -m bootstrap_train.ingest_phase1 --source /path/to/phase1_package --dest-root data/phase1_packages
```

### Main run / train / serve path
```bash
PYTHONPATH=src python -m bootstrap_train.train --config configs/train/phase1_smoke.yaml --dataset-root /path/to/phase1_package
```

### Secondary workflow(s)
```bash
PYTHONPATH=src python -m bootstrap_train.inspect_phase2 --source /path/to/phase2_package
PYTHONPATH=src python -m bootstrap_train.export --config configs/export/onnx_fp32.yaml --weights /path/to/best.pt
```

### Evaluate / validate
```bash
PYTHONPATH=src python -m bootstrap_train.validate_packages --phase1 /path/to/phase1_package
PYTHONPATH=src python -m bootstrap_train.evaluate --config configs/train/phase1_eval.yaml --dataset-root /path/to/phase1_package --weights /path/to/best.pt
```

Notes:
- Use the upstream phase 1 package root, not an arbitrary copy of individual images/labels.
- Prefer single-GPU smoke validation first, then move to `device=0,1,2` only after the single-GPU run is clean.
- Prefer the repo wrapper over raw `yolo detect train` because the wrapper materializes Ultralytics-safe dataset and split files with absolute paths.
- Use `docs/handoffs/` for durable edge/desktop coordination and treat `.agent/` as scratch only.

---

## Metadata contracts (important)
- Phase 1 training-ready package contract:
  - `<phase1_root>/dataset.yaml` must remain Ultralytics-compatible and reference `splits/train.txt` and `splits/val.txt`
  - `<phase1_root>/images/*.jpg` and `<phase1_root>/labels/*.txt` stay 1:1 aligned
  - `<phase1_root>/manifest.json` preserves package/source/entry provenance fields from the Xavier producer
- Phase 2 provenance package contract:
  - `<phase2_root>/manifest.json` preserves package/source/clip provenance
  - `<phase2_root>/clips/<package_clip_id>/` must contain `clip.mp4`, `clip_manifest.json`, `detections.parquet`, and `tracks.parquet`
- Metadata behavior:
  - Validators should fail loudly on missing required fields instead of inventing defaults
  - CLI overrides may replace config defaults, but they must not mutate upstream manifests
  - Training/eval wrappers may generate temporary `.ultralytics_*` files inside a phase 1 package root to normalize paths for Ultralytics; these are consumer-side shims, not upstream contract changes
- Runtime invariants:
  - `person` is the current target class for phase 1 bootstrap training
  - Provenance survives ingest, validation, training metadata, and export stubs

---

## Tests (default)
Run the fastest meaningful checks first:
```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

If the repo has special runtime issues, document the workaround here:
```bash
PYTHONPATH=src python -m compileall src tests
```

Optional additional checks:
```bash
PYTHONPATH=src python -m bootstrap_train.train --config configs/train/phase1_smoke.yaml --dataset-root /path/to/phase1_package --dry-run
PYTHONPATH=src python -m unittest tests.test_contract_artifacts -v
```

---

## Coding/style conventions
- Target Python 3.10 on Ubuntu 22.04.
- Keep validators and config parsing stdlib-first so the repo can bootstrap before optional training dependencies are installed.
- Prefer minimal, localized diffs; avoid broad formatting-only changes unless requested.
- Preserve relative dataset paths and manifest field names exactly unless a task explicitly changes the package contract.
- If no single formatter/linter is enforced, follow existing local style in touched files.

---

## Working agreement (four-phase execution)
### Phase 1 — Plan + Task Definition
Goal: build repo-aware understanding and produce **one** task artifact.

Rules:
- Do not edit code or tracked files in this phase.
- Use ≤10 shell commands and keep output concise (avoid long listings).
- Restate goal + success criteria.
- Identify the minimal relevant files and why.
- Propose a plan + verification commands.

**Phase 1 output (the only artifact):**
- Create a branch for the task using a short name reflecting the goal of the task e.g. `add-oAuth`, `fix-callbacks`
- Write the plan to: `.agent/TASK_BRIEF.md`

`.agent/` is **untracked** and exists specifically for this ephemeral brief. The brief may be updated in Phase 2.

At the end of Phase 1:
- Ensure `.agent/TASK_BRIEF.md` is up to date.

Notes:
  - A template for `.agent/TASK_BRIEF.md` is already available and it is copied from `docs/agent/TASK_BRIEF_TEMPLATE.md`

### Phase 2 — Implement + Learn (write + verify, no git history operations)
Goal: Execute the plan developed in Phase 1 and memorialized in `.agent/TASK_BRIEF.md`

Rules:
- You may edit files, but do NOT run:
  `git commit`, `git push`, `git merge`/`rebase`, `git reset --hard`, `git clean -fd`
- Keep diffs minimal; no broad “format-only” changes unless requested.
- After each coherent edit set:
  1) state intent + files touched
  2) apply changes
  3) run verification and report results
  4) show diff summary and key hunks

## Phase 3 — Debug mode
Goal: Review the output of Phase 2 and thoroughly test until all outputs are predictable and functional.

When debugging bugs introduced during Phase 2, follow this strict loop:
1) Reproduce the failure with the exact command provided.
2) Minimize the repro (smallest failing command/test).
3) Propose 1–2 hypotheses and what evidence would confirm each.
4) Add a targeted regression test when feasible.
5) Make a **surgical** fix (minimal files), re-run the failing test(s), then broaden coverage.
6) Update `.agent/TASK_BRIEF.md` with what changed and why

## Phase 4 — Task completion / closeout procedure
Goal: Summary successful completed work and clean up.

When the task is complete (as defined in `.agent/TASK_BRIEF.md`), the agent should:
1) Review this `AGENTS.md`.
2) Produce a **closeout summary** (short, high-signal), using `.agent/MEMORY.md` and `.agent/TASK_BRIEF.md` as the sources of truth:
   - Decisions made (and why)
   - New invariants/gotchas discovered
   - New/changed commands (CLI flags, scripts)
   - TODOs / follow-ups
   - Verification evidence (commands run)
3) Update repo docs **only when the information is stable and reusable**:
   - Update `AGENTS.md` for durable workflow/invariants only.
   - Update `docs/PROJECT_STATE.md` for “current operational workflow.”
   - Update `docs/MODULE_MAP.md` if module boundaries/entrypoints changed.
   - Update `docs/METRICS_AND_DIAGNOSTICS.md` if diagnostics/metrics interpretation changed.
   - Finish with `git status` and commit message(s)
   - commit code
4) Follow the procedure defined in `Cleanup at task closeout` (defined below)

### Cleanup at task closeout
At completion:
1. Summarize “gotchas / decisions / commands / TODOs” and promote them to durable docs (see `Task completion / closeout procedure`).
2. Create a folder `docs/agent/tasks/<task_slug>` under `docs/agent/tasks`
  - e.g. <task_slug> = YYYYMMDD_HHMM_<short_topic>
3. Move `.agent/TASK_BRIEF.md` to `docs/agent/tasks/<task_slug>/`
4. Move `.agent/MEMORY.md` to `docs/agent/tasks/<task_slug>/`
5. Empty `.agent/logs/` (or delete the directory contents)
6. Write the closeout into `docs/agent/tasks/<task_slug>/CLOSEOUT.md`
7. Verify: `.agent/TASK_BRIEF.md` and `.agent/MEMORY.md` exist (templates), `.agent/logs/` empty, and archive folder contains `TASK_BRIEF.md`, `MEMORY.md`, and `CLOSEOUT.md`

---

## `.agent/` folder policy (scratch only)

`.agent/` is **untracked** and is intended as **scratch space only**. It should be safe to delete at any time, and it should be **cleared at task closeout**.

### Purpose
1) **Task Related documents** most notably TASK_BRIEF.md
2) **User-provided artifacts for debugging** (logs, traces, perf output) that the agent should inspect.
3) **Agent working memory externalization** when the chat context window is under pressure.

> Policy: when the agent learns a new *gotcha* during Phase 2, it should record it in `.agent/MEMORY.md` and only promote it to durable docs during closeout.

### Flat structure (preferred)
- `.agent/TASK_BRIEF.md` — compact task description, success criteria, and progress notes
- `.agent/MEMORY.md` — compact running notes related to the work process rather than the task definition itself
- `.agent/logs/` — log files and small extracted snippets

### `.agent/TASK_BRIEF.md`
During Phase 2 this document may be updated to reflect changes in:

- **Goal / status**
- **Decisions (and why)**
- **Next steps**

### `.agent/MEMORY.md` format (keep it small)
Maintain **≤ 200 lines** when possible. Use bullets. Suggested headings:

- **A valuable research url cache**
- **Repro commands**
- **Hypotheses + evidence**
- **Failed experiments and ideas**
- **Gotchas discovered**  ← (promote these during closeout)
- **Verification run** (commands + outcomes)

Notes:
  - A template for `.agent/MEMORY.md` is already available and it is copied from `docs/agent/MEMORY_TEMPLATE.md`

### Log naming convention
Store logs as:

- `.agent/logs/YYYYMMDD_HHMM_<topic>.log`

The agent may create filtered snippets alongside logs, e.g.:

- `.agent/logs/YYYYMMDD_HHMM_<topic>__excerpt.log`
- `.agent/logs/YYYYMMDD_HHMM_<topic>__grep_<pattern>.log`

Keep snippets **small** (e.g., ≤ 500 lines). Do not copy huge logs.

### When to externalize to `.agent/`
Externalize (write/update `.agent/MEMORY.md`) when any of these is true:
- The plan has evolved materially beyond Phase 1.
- Debugging involves multiple hypotheses or long traces.
- The session is getting long (check `/status` or a token status line).
- The agent is about to run `/compact`.

After externalizing:
- Update `.agent/MEMORY.md`
- Then run `/compact` to keep interactive context focused.

---

## Docs policy (protect the context window)
Do NOT read the entire docs tree by default.

Open docs only when needed, in this priority order:
1) The repo’s current workflow / operational workflow doc
2) The repo’s module / architecture map doc
3) The repo’s metrics / diagnostics doc
4) The repo’s experiment log / change log / results log

Treat these as historical unless explicitly requested:
- old specs
- old work plans
- archived project-state headers
- other superseded planning docs

If the repo does not yet have durable docs in these roles, ask the user which files are intended to fill them.
