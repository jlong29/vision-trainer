# Package Contracts

This repo consumes upstream package types produced on the Xavier NX and curated releases produced by `vision-curator`. Those contracts are treated as durable inputs and must not be silently reshaped.

Machine-readable versions of the manifest contracts live under `schemas/` and must stay aligned with `src/bootstrap_train/validate_packages.py`.

## Phase 1: direct training input

Phase 1 is the current Ultralytics-ready dataset contract.

Expected layout:

```text
<phase1_root>/
├─ dataset.yaml
├─ images/
├─ labels/
├─ manifest.json
└─ splits/
   ├─ train.txt
   └─ val.txt
```

Required behavior:

- `dataset.yaml` remains compatible with Ultralytics detection training.
- `images/` and `labels/` stay 1:1 aligned.
- `splits/train.txt` and `splits/val.txt` contain relative image paths.
- `manifest.json` preserves package, source, and entry provenance.
- For direct raw Ultralytics CLI usage, prefer a dataset YAML whose `path` resolves to the absolute package root. Some Ultralytics versions also mis-handle split files that list relative image paths. The repo wrapper works around both issues by generating normalized temporary inputs for Ultralytics while preserving the upstream package contract unchanged.

Important manifest fields:

- Top-level: `package_id`, `created_at`, `source_directory`, `source_count`, `image_count`, `label_count`, `train_image_count`, `val_image_count`, `class_map`, `sources`, `entries`
- Per-source: `source_path`, `clip_id`, `run_id`, `vision_job_id`, `dataset_root`, `image_count`, `train_image_count`, `val_image_count`, `selection_reason`
- Per-entry: `image_path`, `label_path`, `split`, `frame_num`, `timestamp_sec`, `source_timestamp_sec`, `target_detection_count`, `source_path`, `source_clip_id`, `source_run_id`, `source_vision_job_id`

## Phase 2: provenance and temporal context

Phase 2 is the context-rich clip package. It is readable and inspectable in v1, but it is not the first direct training contract.

Expected layout:

```text
<phase2_root>/
├─ manifest.json
└─ clips/
   ├─ <package_clip_id>/
   │  ├─ clip.mp4
   │  ├─ clip_manifest.json
   │  ├─ detections.parquet
   │  └─ tracks.parquet
   └─ ...
```

Required behavior:

- Package-level `manifest.json` preserves package, source, and clip provenance.
- Every included clip directory contains the stable artifact set.
- Any future clip-to-frame conversion must preserve provenance back to `source_path`, `clip_id`, `run_id`, and `vision_job_id`.

Important manifest fields:

- Top-level: `package_type`, `package_version`, `package_id`, `created_at`, `source_directory`, `source_count`, `clip_count`, `bundle_contract`, `sources`, `clips`
- Per-source: `source_path`, `clip_id`, `run_id`, `run_dir`, `vision_job_id`, `selected`, `selection_reason`, `frame_count`, `detection_count`, `track_count`, `bundle_dir`, `included_in_package`, `package_clip_id`, `package_clip_dir`
- Per-clip: `package_clip_id`, `package_clip_dir`, `source_path`, `clip_id`, `run_id`, `vision_job_id`, `selection_reason`, `created_at`, `start_ts`, `end_ts`, `fps`, `frame_count`, `width`, `height`, `detection_count`, `track_count`, `model_version`, `tracker_type`, `artifacts`

## Curated release: downstream training input

A curated release is the trainer-side contract emitted by `vision-curator`. It is the preferred input for curated smoke training once curator output exists. Phase 1 remains the fallback bootstrap input.

Expected layout:

```text
<release_root>/
├─ dataset.yaml
├─ images/
├─ labels/
├─ manifest.json
├─ provenance/
│  └─ records.jsonl
└─ splits/
   ├─ train.txt
   ├─ val.txt
   └─ test.txt
```

`splits/test.txt` and `provenance/records.jsonl` are optional at the file-layout level, but they are required when `dataset.yaml` or `manifest.json` promises them.

Required behavior:

- `dataset.yaml` remains compatible with Ultralytics detection training.
- Split files contain image paths that resolve inside the release root unless they are absolute paths.
- Referenced images and labels must exist and remain 1:1 aligned for training/eval consumption.
- `manifest.json` preserves release provenance back to source package IDs and annotation versions.
- `provenance/records.jsonl` files named by `manifest.json` must exist.
- The trainer wrapper may generate `.ultralytics_*` shims inside the release root to normalize paths for Ultralytics; these are consumer-side files and not part of the curated release contract.

Important manifest fields:

- Top-level: `release_id`, `source_package_ids`, `annotation_versions`, `split_policy`, `label_policy`, `class_list`, `counts_by_split`, `counts_by_label_source`, `created_at`
- Optional provenance pointer: `provenance_records`

## Operating rule

Phase 1 trains now and remains a fallback. Curated releases become the preferred trainer input after `vision-curator` emits them. Phase 2 explains and extends the source trail.
