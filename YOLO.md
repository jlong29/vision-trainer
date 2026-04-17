# YOLO Bootstrap Training Plan

Audience: the user and Codex building the desktop training repo.

This document is the current source-of-truth handoff between:
- the Xavier NX edge node, which already performs bounded detection, tracking, and packaging
- the Ubuntu 22.04 desktop training machine, which will own dataset curation, training, evaluation, and model promotion

It replaces older draft assumptions that were too focused on generic YOLO hardware notes and not grounded enough in the validated edge workflow we now have.

---

## 1. Executive summary

### System split

**Xavier NX edge node responsibilities**
- run deployed person detection on thermal video through `vision_api`
- package selected results through `thermal-data-engine`
- preserve provenance, track summaries, and clip artifacts
- generate training-facing handoff packages

**Desktop training node responsibilities**
- ingest handoff packages from the Xavier NX
- curate, audit, split, and version datasets
- run Ultralytics YOLO training and evaluation
- compare experiments and promote candidate models
- export deployable artifacts for the Xavier NX runtime

### Current state of the edge work

The Xavier NX side is no longer speculative.

It already has:
- a working `vision_api` detector/runtime boundary
- a working `thermal-data-engine` packaging layer
- a validated **phase 1 image dataset package** for Ultralytics-style training
- a validated **phase 2 temporal video package** for future track-aware work

### Immediate training recommendation

For the first bootstrap training repo, **treat phase 1 as the primary training input**.

Use phase 2 as:
- provenance-rich review material
- future temporal/track-aware research input
- a debugging aid when phase 1 labels need context

Do **not** block the first training repo on temporal modeling.

---

## 2. Current validated desktop training environment

The user has already validated the following on the Ubuntu 22.04 training machine:

- OS: Ubuntu 22.04.5 LTS
- Kernel: `6.8.0-90-generic`
- Driver: `580.95.05`
- `nvidia-smi` CUDA runtime: `13.0`
- Python: `3.10.12`
- GPUs: `3 x NVIDIA GeForce GTX 1080 Ti`
- Torch: `2.6.0+cu126`
- TorchVision: `0.21.0+cu126`
- TorchAudio: `2.6.0+cu126`
- CUDA available from PyTorch: `True`
- GPU count from PyTorch: `3`
- NCCL available: `True`

This means the desktop already has the important base pieces needed for Ultralytics training.

### Practical interpretation

- The current Torch install is good enough to proceed.
- There is **no current need** to rebuild PyTorch or install a different CUDA toolkit just to start YOLO training.
- The next step is to install `ultralytics` into the same `yolo11` conda environment and validate training with that stack.

---

## 3. Recommended install plan for the desktop repo

This is the plan a third party should follow unless a concrete compatibility issue appears.

### 3.1 Create and activate the environment

```bash
conda create -n yolo11 python=3.10 -y
conda activate yolo11
```

### 3.2 Install the already-chosen PyTorch stack

```bash
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu126
```

### 3.3 Install Ultralytics and basic support packages

```bash
pip install -U ultralytics
pip install -U pyyaml pandas matplotlib seaborn tqdm
```

Optional but useful:

```bash
pip install -U tensorboard
```

### 3.4 Validate the install

```bash
python - <<'PY'
import torch
import ultralytics
print('torch:', torch.__version__)
print('torch cuda:', torch.version.cuda)
print('cuda available:', torch.cuda.is_available())
print('gpu count:', torch.cuda.device_count())
print('nccl available:', torch.distributed.is_nccl_available())
print('ultralytics:', ultralytics.__version__)
for i in range(torch.cuda.device_count()):
    print(i, torch.cuda.get_device_name(i))
PY
```

Expected outcome:
- `cuda available: True`
- `gpu count: 3`
- `nccl available: True`
- Ultralytics imports successfully

### 3.5 Validate Ultralytics itself

```bash
yolo checks
```

Then run a minimal smoke test once the repo exists and a dataset is available.

---

## 4. Recommended desktop training configuration

### 4.1 Multi-GPU mode

Use Ultralytics multi-GPU training with:
- `device=0,1,2`
- DDP-style launch through Ultralytics
- one shared conda env on the training host

### 4.2 Initial training defaults

For the first real training runs, start conservatively:

- model family: `yolo11n` or `yolo11s` for pipeline validation
- then move to `yolo11m` if throughput and VRAM are acceptable
- image size: `640`
- workers: start around `8`
- batch: start modestly, then increase after one successful epoch
- AMP: leave enabled unless Pascal-specific instability appears

Example first-pass command:

```bash
yolo detect train \
  model=yolo11s.pt \
  data=/path/to/dataset.yaml \
  imgsz=640 \
  epochs=50 \
  batch=24 \
  device=0,1,2 \
  workers=8 \
  project=runs/train \
  name=bootstrap_yolo11s_phase1
```

Then step up only after confirming:
- all 3 GPUs are used
- there are no OOM failures
- throughput is stable
- temperatures are acceptable

### 4.3 Operational caution for this host

The provided `nvidia-smi` snapshot already showed the 1080 Ti cards running hot under other workloads.

Practical implications:
- watch temperature closely during first DDP runs
- avoid starting with an aggressive batch size
- prefer a clean machine during validation
- if needed, reserve GPU 0 less aggressively because it is also driving display output

If training instability appears, the first knobs to reduce are:
- batch size
- workers
- image size

---

## 5. What the new desktop repo should do

The new repo should be a **desktop training and curation repo**, not a duplicate of `vision_api` or `thermal-data-engine`.

### In scope

- ingest handoff packages from the Xavier NX
- validate package structure before training
- materialize training datasets in repo-controlled locations
- define experiment configs
- run Ultralytics training/eval
- generate reports and comparison summaries
- export deployable artifacts for later promotion back to the Xavier NX

### Out of scope

- reimplement Xavier DeepStream runtime control
- replace `vision_api`
- replace `thermal-data-engine`
- own live edge inference

### Recommended mental model

The desktop repo is the **consumer and curator** of edge-generated packages.

The Xavier NX remains the **producer**.

---

## 6. Edge pipeline status that the desktop repo should assume

The edge stack has already validated the following:

### `vision_api`
- bounded offline detection jobs
- local runtime boundary for Xavier NX inference
- stable job manifests and status handling
- dataset package generation for image-based handoff

### `thermal-data-engine`
- folder-level packaging over `datasets/incoming`
- validated phase 1 Ultralytics-style image package
- validated phase 2 temporal video package
- provenance-preserving manifests

### Important edge-side heuristics already baked in
- suspicious or inflated source fps can trigger duration-based bounding
- `27 fps` is the chosen fallback assumption for the physical thermal camera when metadata is unreliable
- phase 1 training-oriented sampling uses denser extraction than the earlier conservative smoke sample

The desktop repo should treat those as upstream facts, not re-derive them from scratch.

---

## 7. Phase 1 package contract, direct training input

Phase 1 is the **current direct Ultralytics training contract**.

### Package purpose

A single combined image dataset suitable for immediate YOLO detection training.

### Current validated package

Path:

```text
/home/myclaw/.openclaw/workspace/outputs/thermal_data_engine/ultralytics_packages/incoming-training-sample
```

Validated counts:
- `image_count: 1519`
- `label_count: 1519`
- `object_count: 1557`
- `train: 1215`
- `val: 304`

### Directory schema

```text
<ultralytics_package_root>/
├─ dataset.yaml
├─ images/
├─ labels/
├─ manifest.json
└─ splits/
   ├─ train.txt
   └─ val.txt
```

### File contract

#### `dataset.yaml`
Must remain compatible with Ultralytics YOLO detection training.

Expected shape:

```yaml
path: .
train: splits/train.txt
val: splits/val.txt
names:
  0: person
```

#### `images/`
- one JPEG per training example
- filenames are remapped to avoid collisions across source videos

#### `labels/`
- one YOLO `.txt` file per image
- normalized YOLO detection rows
- current target class is `person`

#### `splits/train.txt` and `splits/val.txt`
- newline-delimited relative image paths
- define the train/val split consumed by Ultralytics

#### `manifest.json`
This is the provenance layer and should be preserved.

Important top-level fields:
- `package_id`
- `created_at`
- `source_directory`
- `source_count`
- `image_count`
- `label_count`
- `train_image_count`
- `val_image_count`
- `class_map`
- `sources`
- `entries`

Important per-source fields:
- `source_path`
- `clip_id`
- `run_id`
- `vision_job_id`
- `dataset_root`
- `image_count`
- `train_image_count`
- `val_image_count`
- `selection_reason`

Important per-entry fields:
- `image_path`
- `label_path`
- `split`
- `frame_num`
- `timestamp_sec`
- `source_timestamp_sec`
- `target_detection_count`
- `source_path`
- `source_clip_id`
- `source_run_id`
- `source_vision_job_id`

### How the desktop repo should use phase 1

Use phase 1 directly for:
- first Ultralytics smoke tests
- first supervised fine-tuning runs
- baseline experiment tracking
- error analysis on false positives / false negatives

---

## 8. Phase 2 package contract, temporal/provenance package

Phase 2 is **not** the first direct Ultralytics training contract.
It is the richer temporal handoff contract.

### Package purpose

Preserve temporal structure, clip boundaries, track continuity artifacts, and provenance strongly enough to support:
- review with context
- future track-aware dataset derivation
- debugging and relabeling workflows
- later temporal modeling experiments

### Current validated package

Path:

```text
/home/myclaw/.openclaw/workspace/outputs/thermal_data_engine/video_packages/incoming-video-sample
```

Validated counts:
- `clip_count: 3`
- `source_count: 3`
- `selected_source_count: 3`
- structural validation: `ok: true`

### Directory schema

```text
<video_package_root>/
├─ manifest.json
└─ clips/
   ├─ <package_clip_id>/
   │  ├─ clip.mp4
   │  ├─ clip_manifest.json
   │  ├─ detections.parquet
   │  └─ tracks.parquet
   └─ ...
```

### Package-level `manifest.json`

Important top-level fields:
- `package_type: thermal_video_clip_dataset`
- `package_version: v1`
- `package_id`
- `created_at`
- `source_directory`
- `source_count`
- `clip_count`
- `bundle_contract`
- `sources`
- `clips`

Important per-source fields:
- `source_path`
- `clip_id`
- `run_id`
- `run_dir`
- `vision_job_id`
- `selected`
- `selection_reason`
- `frame_count`
- `detection_count`
- `track_count`
- `bundle_dir`
- `included_in_package`
- `package_clip_id`
- `package_clip_dir`

Important per-clip fields:
- `package_clip_id`
- `package_clip_dir`
- `source_path`
- `clip_id`
- `run_id`
- `vision_job_id`
- `selection_reason`
- `created_at`
- `start_ts`
- `end_ts`
- `fps`
- `frame_count`
- `width`
- `height`
- `detection_count`
- `track_count`
- `model_version`
- `tracker_type`
- `artifacts`

### Clip-level artifact contract

Each included clip directory contains the stable bundle contract:
- `clip.mp4`
- `clip_manifest.json`
- `detections.parquet`
- `tracks.parquet`

### How the desktop repo should use phase 2

Use phase 2 for:
- context-aware review of phase 1 samples
- relabeling support when frame-only labels are ambiguous
- future clip-to-frame extraction logic
- future temporal experiments

Do **not** treat phase 2 as the initial direct training contract unless the repo explicitly adds a converter that materializes a training-ready representation from it.

---

## 9. Dataset contract summary for third parties

If someone asks, “What exactly does the Xavier produce for YOLO training?”, the answer is:

### Phase 1, training-ready
A combined Ultralytics-style detection dataset:
- `dataset.yaml`
- `images/*.jpg`
- `labels/*.txt`
- `splits/train.txt`
- `splits/val.txt`
- `manifest.json`

This is the current direct contract for Ultralytics YOLO detection training.

### Phase 2, context-rich
A clip-scoped temporal package:
- package `manifest.json`
- one subdirectory per selected clip
- each clip contains `clip.mp4`, `clip_manifest.json`, `detections.parquet`, `tracks.parquet`

This is the current contract for provenance, review context, and future temporal work.

### Key rule

**Phase 1 trains now. Phase 2 explains and extends phase 1.**

---

## 10. Recommended desktop repo structure

The desktop repo should assume the edge repos already exist and should focus on consuming their outputs.

```text
repo/
├─ AGENTS.md
├─ README.md
├─ pyproject.toml
├─ configs/
│  ├─ train/
│  ├─ data/
│  └─ export/
├─ docs/
│  ├─ package_contracts.md
│  ├─ training_workflow.md
│  ├─ experiment_policy.md
│  └─ promotion_workflow.md
├─ src/
│  ├─ bootstrap_train/
│  │  ├─ ingest_phase1.py
│  │  ├─ inspect_phase2.py
│  │  ├─ validate_packages.py
│  │  ├─ train.py
│  │  ├─ evaluate.py
│  │  ├─ export.py
│  │  └─ manifests.py
├─ scripts/
│  ├─ validate_env.sh
│  ├─ train_phase1_smoke.sh
│  └─ export_candidate.sh
└─ tests/
```

### First repo tasks for Codex

1. Create environment and validation instructions.
2. Add package validators for phase 1 and phase 2.
3. Add a config-driven training entrypoint for phase 1 datasets.
4. Add experiment output conventions.
5. Add export/promotion stubs for later Xavier deployment.

---

## 11. Concrete validation workflow for the new repo

### Environment validation

```bash
python - <<'PY'
import torch
import ultralytics
print(torch.cuda.is_available())
print(torch.cuda.device_count())
print(ultralytics.__version__)
PY

yolo checks
```

### Dataset validation

The repo should validate before training:
- `dataset.yaml` exists
- referenced train/val paths exist
- every image has a label file
- YOLO label rows are normalized
- manifest provenance is preserved

### First training smoke test

Run one short training job against the phase 1 package.

Example:

```bash
yolo detect train \
  model=yolo11n.pt \
  data=/home/myclaw/.openclaw/workspace/outputs/thermal_data_engine/ultralytics_packages/incoming-training-sample/dataset.yaml \
  imgsz=640 \
  epochs=5 \
  batch=12 \
  device=0 \
  project=runs/train \
  name=phase1_smoke_single_gpu
```

Then move to multi-GPU only after the single-GPU smoke test is clean.

### First multi-GPU smoke test

```bash
yolo detect train \
  model=yolo11n.pt \
  data=/home/myclaw/.openclaw/workspace/outputs/thermal_data_engine/ultralytics_packages/incoming-training-sample/dataset.yaml \
  imgsz=640 \
  epochs=5 \
  batch=24 \
  device=0,1,2 \
  workers=8 \
  project=runs/train \
  name=phase1_smoke_ddp
```

---

## 12. Guidance for Codex

If Codex is building the new repo, it should assume:

- the Xavier NX edge packaging work already exists and should not be rebuilt
- the first consumer is the phase 1 Ultralytics package
- phase 2 should be supported as a readable/inspectable input, not necessarily as the first trainable format
- provenance matters and should survive every copy or transformation
- the repo should optimize for repeatable bootstrap training, not generic framework sprawl

### Non-goals for the first iteration

- no CVAT integration in v1 unless explicitly requested
- no temporal model training in v1 unless explicitly requested
- no duplication of Xavier runtime code in the desktop repo
- no premature support for many model families

### v1 success criteria

- install is reproducible on the desktop host
- phase 1 package validates and trains successfully
- multi-GPU training works on `device=0,1,2`
- outputs are organized well enough to compare experiments
- the repo can export a candidate model for later deployment testing

---

## 13. Immediate next step

Build the desktop repo around this sequence:

1. validate environment
2. ingest and validate the phase 1 package
3. run a single-GPU training smoke test
4. run a 3-GPU smoke test
5. add experiment tracking/report outputs
6. add phase 2 inspection tools
7. add export/promotion support

That is the shortest path from the current Xavier NX work to a real bootstrap training loop.
