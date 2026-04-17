from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bootstrap_train.validate_packages import validate_phase1_package, validate_phase2_package


def build_phase1_package(root: Path) -> Path:
    (root / "images").mkdir(parents=True)
    (root / "labels").mkdir(parents=True)
    (root / "splits").mkdir(parents=True)

    (root / "dataset.yaml").write_text(
        "\n".join(
            [
                "path: .",
                "train: splits/train.txt",
                "val: splits/val.txt",
                "names:",
                "  0: person",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "images" / "frame_0001.jpg").write_bytes(b"jpeg")
    (root / "images" / "frame_0002.jpg").write_bytes(b"jpeg")
    (root / "labels" / "frame_0001.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    (root / "labels" / "frame_0002.txt").write_text("0 0.4 0.4 0.1 0.1\n", encoding="utf-8")
    (root / "splits" / "train.txt").write_text("images/frame_0001.jpg\n", encoding="utf-8")
    (root / "splits" / "val.txt").write_text("images/frame_0002.jpg\n", encoding="utf-8")

    manifest = {
        "package_id": "phase1-sample",
        "created_at": "2026-04-17T00:00:00Z",
        "source_directory": "/tmp/source",
        "source_count": 1,
        "image_count": 2,
        "label_count": 2,
        "train_image_count": 1,
        "val_image_count": 1,
        "object_count": 2,
        "class_map": {"0": "person"},
        "sources": [
            {
                "source_path": "/tmp/source/video.mp4",
                "clip_id": "clip-1",
                "run_id": "run-1",
                "vision_job_id": "job-1",
                "dataset_root": "/tmp/source",
                "image_count": 2,
                "train_image_count": 1,
                "val_image_count": 1,
                "selection_reason": "bootstrap",
            }
        ],
        "entries": [
            {
                "image_path": "images/frame_0001.jpg",
                "label_path": "labels/frame_0001.txt",
                "split": "train",
                "frame_num": 1,
                "timestamp_sec": 0.1,
                "source_timestamp_sec": 0.1,
                "target_detection_count": 1,
                "source_path": "/tmp/source/video.mp4",
                "source_clip_id": "clip-1",
                "source_run_id": "run-1",
                "source_vision_job_id": "job-1",
            },
            {
                "image_path": "images/frame_0002.jpg",
                "label_path": "labels/frame_0002.txt",
                "split": "val",
                "frame_num": 2,
                "timestamp_sec": 0.2,
                "source_timestamp_sec": 0.2,
                "target_detection_count": 1,
                "source_path": "/tmp/source/video.mp4",
                "source_clip_id": "clip-1",
                "source_run_id": "run-1",
                "source_vision_job_id": "job-1",
            },
        ],
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root


def build_phase2_package(root: Path) -> Path:
    clip_dir = root / "clips" / "package-clip-1"
    clip_dir.mkdir(parents=True)
    for filename in ["clip.mp4", "clip_manifest.json", "detections.parquet", "tracks.parquet"]:
        (clip_dir / filename).write_bytes(b"")

    manifest = {
        "package_type": "thermal_video_clip_dataset",
        "package_version": "v1",
        "package_id": "phase2-sample",
        "created_at": "2026-04-17T00:00:00Z",
        "source_directory": "/tmp/source",
        "source_count": 1,
        "clip_count": 1,
        "bundle_contract": "v1",
        "sources": [
            {
                "source_path": "/tmp/source/video.mp4",
                "clip_id": "clip-1",
                "run_id": "run-1",
                "run_dir": "/tmp/run-1",
                "vision_job_id": "job-1",
                "selected": True,
                "selection_reason": "bootstrap",
                "frame_count": 32,
                "detection_count": 8,
                "track_count": 2,
                "bundle_dir": "/tmp/bundle",
                "included_in_package": True,
                "package_clip_id": "package-clip-1",
                "package_clip_dir": "clips/package-clip-1",
            }
        ],
        "clips": [
            {
                "package_clip_id": "package-clip-1",
                "package_clip_dir": "clips/package-clip-1",
                "source_path": "/tmp/source/video.mp4",
                "clip_id": "clip-1",
                "run_id": "run-1",
                "vision_job_id": "job-1",
                "selection_reason": "bootstrap",
                "created_at": "2026-04-17T00:00:00Z",
                "start_ts": 0.0,
                "end_ts": 3.0,
                "fps": 27.0,
                "frame_count": 32,
                "width": 640,
                "height": 512,
                "detection_count": 8,
                "track_count": 2,
                "model_version": "phase2-model",
                "tracker_type": "bytetrack",
                "artifacts": {
                    "clip": "clip.mp4",
                    "detections": "detections.parquet",
                    "tracks": "tracks.parquet",
                },
            }
        ],
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root


class ValidatePackagesTest(unittest.TestCase):
    def test_validate_phase1_package_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report = validate_phase1_package(build_phase1_package(Path(tmp_dir)))
            self.assertTrue(report.ok, report.errors)
            self.assertEqual(report.counts["image_files"], 2)
            self.assertEqual(report.counts["object_count"], 2)

    def test_validate_phase1_package_rejects_bad_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = build_phase1_package(Path(tmp_dir))
            (root / "labels" / "frame_0002.txt").write_text("0 1.4 0.5 0.1 0.1\n", encoding="utf-8")
            report = validate_phase1_package(root)
            self.assertFalse(report.ok)
            self.assertTrue(any("normalized" in error for error in report.errors))

    def test_validate_phase2_package_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report = validate_phase2_package(build_phase2_package(Path(tmp_dir)))
            self.assertTrue(report.ok, report.errors)
            self.assertEqual(report.counts["clip_dirs"], 1)


if __name__ == "__main__":
    unittest.main()
