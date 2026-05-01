# Training Workflow

## Baseline environment

The desktop host already validated the base environment on April 17, 2026:

- Ubuntu 22.04.5 LTS
- Python 3.10 in the `yolo11` conda environment
- `torch==2.6.0`, `torchvision==0.21.0`, `torchaudio==2.6.0`
- `ultralytics` plus basic support packages
- 3x GTX 1080 Ti visible to PyTorch with NCCL available

Use `scripts/validate_env.sh` to re-check imports and GPU visibility on demand.

## Recommended order

### Phase 1 fallback path

1. Validate the environment.
2. Validate the upstream phase 1 package contract.
3. Ingest the phase 1 package into a repo-controlled location if needed.
4. Run a single-GPU smoke train with `configs/train/phase1_smoke.yaml`.
5. Run a 3-GPU smoke train with `configs/train/phase1_ddp.yaml`.
6. Evaluate the best checkpoint against the same validated dataset.
7. Export a candidate artifact and record the promotion metadata.
8. Use phase 2 inspection to review ambiguous cases or provenance questions.

### Curated release path

Once `vision-curator` emits a release, validate the release before training:

```bash
PYTHONPATH=src python -m bootstrap_train.validate_packages --release /path/to/curated_release
```

Then run a single-GPU smoke train with the curated-release config:

```bash
PYTHONPATH=src python -m bootstrap_train.train --config configs/train/curated_release_smoke.yaml --dataset-root /path/to/curated_release --dry-run
PYTHONPATH=src python -m bootstrap_train.train --config configs/train/curated_release_smoke.yaml --dataset-root /path/to/curated_release
```

The training wrapper accepts `--dataset-kind curated_release` as an explicit override. The curated smoke config already sets `dataset_kind: curated_release`.

Evaluate curated-release-trained weights by passing the same dataset kind:

```bash
PYTHONPATH=src python -m bootstrap_train.evaluate --config configs/train/phase1_eval.yaml --dataset-root /path/to/curated_release --dataset-kind curated_release --weights /path/to/best.pt
```

## Operational cautions

- Start with conservative batch sizes and watch temperature on the 1080 Ti cards.
- Prefer a clean machine during the first DDP validation run.
- If instability appears, reduce `batch`, then `workers`, then `imgsz`.
- GPU 0 may also drive display output, so keep an eye on its thermals and memory pressure.
- Prefer the repo wrapper over raw `yolo detect train` so the dataset YAML and split files are normalized to absolute paths before Ultralytics reads them.
- Curated-release smoke runs are wiring validation until a real `vision-curator` release exists. Do not claim gold validation or hard-case performance from pseudo-only fixtures.
