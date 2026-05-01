from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bootstrap_train.evaluate import prepare_evaluation_command
from bootstrap_train.export import prepare_export_command
from bootstrap_train.train import materialize_ultralytics_dataset_yaml, prepare_training_command

from tests.test_validate_packages import build_curated_release, build_phase1_package


class WorkflowCommandTest(unittest.TestCase):
    def test_prepare_training_command_uses_dataset_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dataset_root = build_phase1_package(Path(tmp_dir) / "phase1")
            prepared = prepare_training_command(
                "configs/train/phase1_smoke.yaml",
                dataset_root=str(dataset_root),
                device="0",
                name="unit_test_train",
            )

            command = prepared["command"]
            self.assertEqual(command[:3], ["yolo", "detect", "train"])
            self.assertTrue(any(arg.startswith("data=") for arg in command))
            self.assertIn("device=0", command)
            self.assertIn("name=unit_test_train", command)
            self.assertTrue(any(arg.endswith("/.ultralytics_dataset.yaml") for arg in command if arg.startswith("data=")))
            self.assertEqual(prepared["dataset_kind"], "phase1")

    def test_materialized_dataset_yaml_uses_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dataset_root = build_phase1_package(Path(tmp_dir) / "phase1")
            shim = materialize_ultralytics_dataset_yaml(dataset_root)
            text = shim.read_text(encoding="utf-8")

            self.assertIn(f"path: {dataset_root.resolve()}", text)
            self.assertIn(f"train: {dataset_root.resolve()}/.ultralytics_splits/train.txt", text)
            self.assertIn(f"val: {dataset_root.resolve()}/.ultralytics_splits/val.txt", text)
            train_split = (dataset_root / ".ultralytics_splits" / "train.txt").read_text(encoding="utf-8")
            val_split = (dataset_root / ".ultralytics_splits" / "val.txt").read_text(encoding="utf-8")
            self.assertIn(str((dataset_root / "images" / "frame_0001.jpg").resolve()), train_split)
            self.assertIn(str((dataset_root / "images" / "frame_0002.jpg").resolve()), val_split)

    def test_prepare_training_command_accepts_curated_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            release_root = build_curated_release(Path(tmp_dir) / "release")
            prepared = prepare_training_command(
                "configs/train/curated_release_smoke.yaml",
                dataset_root=str(release_root),
                name="unit_test_curated_train",
            )

            command = prepared["command"]
            self.assertEqual(command[:3], ["yolo", "detect", "train"])
            self.assertIn("name=unit_test_curated_train", command)
            self.assertEqual(prepared["dataset_kind"], "curated_release")
            self.assertEqual(prepared["source"]["id"], "curated-release-sample")
            self.assertFalse(any(arg.startswith("dataset_kind=") for arg in command))

    def test_prepare_evaluation_command_accepts_curated_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            release_root = build_curated_release(Path(tmp_dir) / "release")
            prepared = prepare_evaluation_command(
                "configs/train/phase1_eval.yaml",
                dataset_root=release_root,
                weights="runs/train/sample/weights/best.pt",
                dataset_kind="curated_release",
                name="unit_test_curated_eval",
            )

            command = prepared["command"]
            self.assertEqual(command[:3], ["yolo", "detect", "val"])
            self.assertIn("name=unit_test_curated_eval", command)
            self.assertEqual(prepared["dataset_kind"], "curated_release")
            self.assertEqual(prepared["source"]["id"], "curated-release-sample")

    def test_prepare_export_command_uses_config_defaults(self) -> None:
        prepared = prepare_export_command(
            "configs/export/onnx_fp32.yaml",
            weights="runs/train/sample/weights/best.pt",
            name="unit_test_export",
        )
        command = prepared["command"]
        self.assertEqual(command[:3], ["yolo", "detect", "export"])
        self.assertIn("format=onnx", command)
        self.assertIn("name=unit_test_export", command)
        self.assertTrue(prepared["export_dir"].endswith("artifacts/exports/unit_test_export"))

    def test_prepare_export_command_records_curated_release_source(self) -> None:
        prepared = prepare_export_command(
            "configs/export/onnx_fp32.yaml",
            weights="runs/train/sample/weights/best.pt",
            name="unit_test_export",
            release_root="tests/fixtures/packages/curated_release_minimal",
        )

        self.assertEqual(prepared["source"]["kind"], "curated_release")
        self.assertEqual(prepared["source"]["id"], "curated-release-sample")
        self.assertEqual(prepared["source"]["details"]["annotation_versions"], ["pseudo-v1"])


if __name__ == "__main__":
    unittest.main()
