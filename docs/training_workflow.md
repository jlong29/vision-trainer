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

1. Validate the environment.
2. Validate the upstream phase 1 package contract.
3. Ingest the phase 1 package into a repo-controlled location if needed.
4. Run a single-GPU smoke train with `configs/train/phase1_smoke.yaml`.
5. Run a 3-GPU smoke train with `configs/train/phase1_ddp.yaml`.
6. Evaluate the best checkpoint against the same validated dataset.
7. Export a candidate artifact and record the promotion metadata.
8. Use phase 2 inspection to review ambiguous cases or provenance questions.

## Operational cautions

- Start with conservative batch sizes and watch temperature on the 1080 Ti cards.
- Prefer a clean machine during the first DDP validation run.
- If instability appears, reduce `batch`, then `workers`, then `imgsz`.
- GPU 0 may also drive display output, so keep an eye on its thermals and memory pressure.
- Prefer the repo wrapper over raw `yolo detect train` so the dataset YAML and split files are normalized to absolute paths before Ultralytics reads them.
