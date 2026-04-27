from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .manifests import ensure_mapping, ensure_required_fields, load_json, load_simple_yaml


PHASE1_TOP_LEVEL_FIELDS = [
    "package_id",
    "created_at",
    "source_directory",
    "source_count",
    "image_count",
    "label_count",
    "train_image_count",
    "val_image_count",
    "class_map",
    "sources",
    "entries",
]
PHASE1_SOURCE_FIELDS = [
    "source_path",
    "clip_id",
    "run_id",
    "vision_job_id",
    "dataset_root",
    "image_count",
    "train_image_count",
    "val_image_count",
    "selection_reason",
]
PHASE1_ENTRY_FIELDS = [
    "image_path",
    "label_path",
    "split",
    "frame_num",
    "timestamp_sec",
    "source_timestamp_sec",
    "target_detection_count",
    "source_path",
    "source_clip_id",
    "source_run_id",
    "source_vision_job_id",
]
PHASE2_TOP_LEVEL_FIELDS = [
    "package_type",
    "package_version",
    "package_id",
    "created_at",
    "source_directory",
    "source_count",
    "clip_count",
    "bundle_contract",
    "sources",
    "clips",
]
PHASE2_SOURCE_FIELDS = [
    "source_path",
    "clip_id",
    "run_id",
    "run_dir",
    "vision_job_id",
    "selected",
    "selection_reason",
    "frame_count",
    "detection_count",
    "track_count",
    "bundle_dir",
    "included_in_package",
    "package_clip_id",
    "package_clip_dir",
]
PHASE2_CLIP_FIELDS = [
    "package_clip_id",
    "package_clip_dir",
    "source_path",
    "clip_id",
    "run_id",
    "vision_job_id",
    "selection_reason",
    "created_at",
    "start_ts",
    "end_ts",
    "fps",
    "frame_count",
    "width",
    "height",
    "detection_count",
    "track_count",
    "model_version",
    "tracker_type",
    "artifacts",
]
PHASE2_REQUIRED_CLIP_FILES = [
    "clip.mp4",
    "clip_manifest.json",
    "detections.parquet",
    "tracks.parquet",
]


@dataclass
class ValidationReport:
    phase: str
    root: str
    ok: bool = True
    counts: dict[str, int] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.ok = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read_split_file(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _normalize_names_mapping(names: Any) -> dict[str, Any]:
    if not isinstance(names, dict):
        return {}
    normalized: dict[str, Any] = {}
    for key, value in names.items():
        normalized[str(key)] = value
    return normalized


def _label_path_for_image(root: Path, image_rel: str) -> Path:
    image_path = Path(image_rel)
    if image_path.parts and image_path.parts[0] == "images":
        return root / Path("labels", *image_path.parts[1:]).with_suffix(".txt")
    return root / "labels" / image_path.with_suffix(".txt").name


def _validate_yolo_label_file(label_path: Path, context: str, report: ValidationReport) -> int:
    object_count = 0
    for line_number, raw_line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue

        parts = stripped.split()
        if len(parts) != 5:
            report.add_error(f"{context}: expected 5 fields, found {len(parts)} on line {line_number}")
            continue

        try:
            class_id = int(parts[0])
        except ValueError:
            report.add_error(f"{context}: invalid class id '{parts[0]}' on line {line_number}")
            continue

        if class_id < 0:
            report.add_error(f"{context}: negative class id on line {line_number}")

        try:
            x_center, y_center, width, height = [float(value) for value in parts[1:]]
        except ValueError:
            report.add_error(f"{context}: non-numeric box values on line {line_number}")
            continue

        for name, value in {
            "x_center": x_center,
            "y_center": y_center,
            "width": width,
            "height": height,
        }.items():
            if not 0.0 <= value <= 1.0:
                report.add_error(f"{context}: {name}={value} must be normalized on line {line_number}")

        if width <= 0.0 or height <= 0.0:
            report.add_error(f"{context}: width/height must be > 0 on line {line_number}")

        object_count += 1

    return object_count


def validate_phase1_package(root: str | Path) -> ValidationReport:
    package_root = Path(root)
    report = ValidationReport(phase="phase1", root=str(package_root.resolve()))

    if not package_root.exists() or not package_root.is_dir():
        report.add_error("phase1 root does not exist or is not a directory")
        return report

    required_paths = [
        package_root / "dataset.yaml",
        package_root / "images",
        package_root / "labels",
        package_root / "manifest.json",
        package_root / "splits" / "train.txt",
        package_root / "splits" / "val.txt",
    ]
    for required in required_paths:
        if not required.exists():
            report.add_error(f"missing required path: {required.relative_to(package_root)}")

    if report.errors:
        return report

    dataset_yaml = load_simple_yaml(package_root / "dataset.yaml")
    report.errors.extend(ensure_required_fields(dataset_yaml, ["train", "val", "names"], "dataset.yaml"))
    report.ok = not report.errors
    if report.errors:
        return report

    dataset_path = dataset_yaml.get("path")
    if dataset_path == ".":
        report.add_warning(
            "dataset.yaml path='.' can fail in raw Ultralytics CLI because relative paths may resolve outside the package root"
        )
    elif dataset_path not in {None, ""}:
        candidate = Path(str(dataset_path))
        if not candidate.is_absolute():
            report.add_warning("dataset.yaml path is relative; prefer an absolute package root for direct Ultralytics CLI")

    names_mapping = _normalize_names_mapping(dataset_yaml.get("names"))
    if names_mapping.get("0") != "person":
        report.add_error("dataset.yaml names[0] must be 'person' for the bootstrap contract")
        return report

    train_rel = str(dataset_yaml["train"])
    val_rel = str(dataset_yaml["val"])
    train_split = package_root / train_rel
    val_split = package_root / val_rel
    if not train_split.exists():
        report.add_error(f"dataset.yaml references missing train split: {train_rel}")
    if not val_split.exists():
        report.add_error(f"dataset.yaml references missing val split: {val_rel}")
    if report.errors:
        return report

    train_images = _read_split_file(train_split)
    val_images = _read_split_file(val_split)
    split_images = train_images + val_images
    object_count = 0

    for image_rel in split_images:
        image_path = package_root / image_rel
        if not image_path.exists():
            report.add_error(f"missing image referenced by split file: {image_rel}")
            continue

        label_path = _label_path_for_image(package_root, image_rel)
        if not label_path.exists():
            report.add_error(f"missing label for image: {image_rel}")
            continue

        object_count += _validate_yolo_label_file(
            label_path,
            f"label {label_path.relative_to(package_root)}",
            report,
        )

    manifest = ensure_mapping(load_json(package_root / "manifest.json"), "manifest.json")
    report.errors.extend(ensure_required_fields(manifest, PHASE1_TOP_LEVEL_FIELDS, "manifest.json"))
    report.ok = not report.errors
    if report.errors:
        return report

    sources = manifest.get("sources", [])
    entries = manifest.get("entries", [])
    if not isinstance(sources, list):
        report.add_error("manifest.json field 'sources' must be a list")
        return report
    if not isinstance(entries, list):
        report.add_error("manifest.json field 'entries' must be a list")
        return report

    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            report.add_error(f"manifest.json sources[{index}] must be a mapping")
            continue
        report.errors.extend(ensure_required_fields(source, PHASE1_SOURCE_FIELDS, f"manifest.json sources[{index}]"))

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            report.add_error(f"manifest.json entries[{index}] must be a mapping")
            continue
        report.errors.extend(ensure_required_fields(entry, PHASE1_ENTRY_FIELDS, f"manifest.json entries[{index}]"))

    image_files = [path for path in (package_root / "images").rglob("*") if path.is_file()]
    label_files = [path for path in (package_root / "labels").rglob("*.txt")]

    report.counts = {
        "train_images": len(train_images),
        "val_images": len(val_images),
        "split_images": len(split_images),
        "image_files": len(image_files),
        "label_files": len(label_files),
        "manifest_sources": len(sources),
        "manifest_entries": len(entries),
        "object_count": object_count,
    }
    report.details = {
        "package_id": manifest.get("package_id"),
        "class_map": manifest.get("class_map"),
    }

    expected_counts = {
        "image_count": len(image_files),
        "label_count": len(label_files),
        "train_image_count": len(train_images),
        "val_image_count": len(val_images),
        "source_count": len(sources),
    }
    for field_name, actual in expected_counts.items():
        manifest_value = manifest.get(field_name)
        if manifest_value != actual:
            report.add_error(f"manifest.json {field_name}={manifest_value} does not match observed count {actual}")

    if manifest.get("image_count") != len(entries):
        report.add_warning("manifest.json image_count does not match entry count")

    if "object_count" in manifest and manifest.get("object_count") != object_count:
        report.add_warning(
            f"manifest.json object_count={manifest.get('object_count')} does not match observed count {object_count}"
        )

    report.ok = not report.errors
    return report


def validate_phase2_package(root: str | Path) -> ValidationReport:
    package_root = Path(root)
    report = ValidationReport(phase="phase2", root=str(package_root.resolve()))

    if not package_root.exists() or not package_root.is_dir():
        report.add_error("phase2 root does not exist or is not a directory")
        return report

    required_paths = [package_root / "manifest.json", package_root / "clips"]
    for required in required_paths:
        if not required.exists():
            report.add_error(f"missing required path: {required.relative_to(package_root)}")
    if report.errors:
        return report

    manifest = ensure_mapping(load_json(package_root / "manifest.json"), "manifest.json")
    report.errors.extend(ensure_required_fields(manifest, PHASE2_TOP_LEVEL_FIELDS, "manifest.json"))
    report.ok = not report.errors
    if report.errors:
        return report

    if manifest.get("package_type") != "thermal_video_clip_dataset":
        report.add_error("manifest.json package_type must be 'thermal_video_clip_dataset'")

    if manifest.get("package_version") != "v1":
        report.add_warning("manifest.json package_version is not 'v1'")

    sources = manifest.get("sources", [])
    clips = manifest.get("clips", [])
    if not isinstance(sources, list):
        report.add_error("manifest.json field 'sources' must be a list")
        return report
    if not isinstance(clips, list):
        report.add_error("manifest.json field 'clips' must be a list")
        return report

    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            report.add_error(f"manifest.json sources[{index}] must be a mapping")
            continue
        report.errors.extend(ensure_required_fields(source, PHASE2_SOURCE_FIELDS, f"manifest.json sources[{index}]"))

    clip_dirs = [path for path in (package_root / "clips").iterdir() if path.is_dir()]
    clip_dir_names = {path.name for path in clip_dirs}
    for index, clip in enumerate(clips):
        if not isinstance(clip, dict):
            report.add_error(f"manifest.json clips[{index}] must be a mapping")
            continue
        report.errors.extend(ensure_required_fields(clip, PHASE2_CLIP_FIELDS, f"manifest.json clips[{index}]"))

        package_clip_id = clip.get("package_clip_id")
        if package_clip_id not in clip_dir_names:
            report.add_error(f"missing clip directory for package_clip_id '{package_clip_id}'")
            continue

        clip_dir = package_root / "clips" / str(package_clip_id)
        for filename in PHASE2_REQUIRED_CLIP_FILES:
            if not (clip_dir / filename).exists():
                report.add_error(f"clip {package_clip_id} missing required file: {filename}")

    report.counts = {
        "manifest_sources": len(sources),
        "manifest_clips": len(clips),
        "clip_dirs": len(clip_dirs),
    }
    report.details = {
        "package_id": manifest.get("package_id"),
        "bundle_contract": manifest.get("bundle_contract"),
    }

    if manifest.get("source_count") != len(sources):
        report.add_error(
            f"manifest.json source_count={manifest.get('source_count')} does not match observed count {len(sources)}"
        )
    if manifest.get("clip_count") != len(clips):
        report.add_error(f"manifest.json clip_count={manifest.get('clip_count')} does not match clip list size")
    if len(clips) != len(clip_dirs):
        report.add_error(f"manifest clip list size {len(clips)} does not match clip directory count {len(clip_dirs)}")

    report.ok = not report.errors
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate phase 1 and phase 2 package contracts.")
    parser.add_argument("--phase1", action="append", default=[], help="Path to a phase 1 package root.")
    parser.add_argument("--phase2", action="append", default=[], help="Path to a phase 2 package root.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.phase1 and not args.phase2:
        parser.error("provide at least one --phase1 or --phase2 path")

    reports: list[ValidationReport] = []
    for root in args.phase1:
        reports.append(validate_phase1_package(root))
    for root in args.phase2:
        reports.append(validate_phase2_package(root))

    payload: Any
    if len(reports) == 1:
        payload = reports[0].to_dict()
    else:
        payload = [report.to_dict() for report in reports]

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if all(report.ok for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
