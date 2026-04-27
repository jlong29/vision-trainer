from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bootstrap_train.export import prepare_export_command
from bootstrap_train.train import materialize_ultralytics_dataset_yaml, prepare_training_command

from tests.test_validate_packages import build_phase1_package


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


if __name__ == "__main__":
    unittest.main()
