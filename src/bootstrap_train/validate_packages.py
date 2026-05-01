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
CURATED_RELEASE_TOP_LEVEL_FIELDS = [
    "release_id",
    "source_package_ids",
    "annotation_versions",
    "split_policy",
    "label_policy",
    "class_list",
    "counts_by_split",
    "counts_by_label_source",
    "created_at",
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


def _dataset_class_list(names: Any) -> list[str]:
    names_mapping = _normalize_names_mapping(names)
    class_names: list[str] = []
    for index in range(len(names_mapping)):
        key = str(index)
        if key not in names_mapping:
            return []
        class_names.append(str(names_mapping[key]))
    return class_names


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


def _ensure_string_list(value: Any, context: str, report: ValidationReport) -> list[str]:
    if not isinstance(value, list):
        report.add_error(f"{context} must be a list")
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            report.add_error(f"{context}[{index}] must be a string")
            continue
        result.append(item)
    return result


def _ensure_int_mapping(value: Any, context: str, report: ValidationReport) -> dict[str, int]:
    if not isinstance(value, dict):
        report.add_error(f"{context} must be a mapping")
        return {}
    result: dict[str, int] = {}
    for key, item in value.items():
        if isinstance(item, bool) or not isinstance(item, int):
            report.add_error(f"{context}.{key} must be an integer")
            continue
        result[str(key)] = item
    return result


def validate_curated_release(root: str | Path) -> ValidationReport:
    release_root = Path(root)
    report = ValidationReport(phase="curated_release", root=str(release_root.resolve()))

    if not release_root.exists() or not release_root.is_dir():
        report.add_error("curated release root does not exist or is not a directory")
        return report

    required_paths = [
        release_root / "dataset.yaml",
        release_root / "manifest.json",
        release_root / "splits" / "train.txt",
        release_root / "splits" / "val.txt",
    ]
    for required in required_paths:
        if not required.exists():
            report.add_error(f"missing required path: {required.relative_to(release_root)}")
    if report.errors:
        return report

    dataset_yaml = load_simple_yaml(release_root / "dataset.yaml")
    report.errors.extend(ensure_required_fields(dataset_yaml, ["train", "val", "names"], "dataset.yaml"))
    report.ok = not report.errors
    if report.errors:
        return report

    manifest = ensure_mapping(load_json(release_root / "manifest.json"), "manifest.json")
    report.errors.extend(ensure_required_fields(manifest, CURATED_RELEASE_TOP_LEVEL_FIELDS, "manifest.json"))
    report.ok = not report.errors
    if report.errors:
        return report

    source_package_ids = _ensure_string_list(
        manifest.get("source_package_ids"),
        "manifest.json source_package_ids",
        report,
    )
    annotation_versions = _ensure_string_list(
        manifest.get("annotation_versions"),
        "manifest.json annotation_versions",
        report,
    )
    class_list = _ensure_string_list(manifest.get("class_list"), "manifest.json class_list", report)
    counts_by_split = _ensure_int_mapping(manifest.get("counts_by_split"), "manifest.json counts_by_split", report)
    counts_by_label_source = _ensure_int_mapping(
        manifest.get("counts_by_label_source"),
        "manifest.json counts_by_label_source",
        report,
    )

    if not isinstance(manifest.get("split_policy"), dict):
        report.add_error("manifest.json split_policy must be a mapping")
    if not isinstance(manifest.get("label_policy"), dict):
        report.add_error("manifest.json label_policy must be a mapping")
    if not source_package_ids:
        report.add_error("manifest.json source_package_ids must not be empty")
    if not annotation_versions:
        report.add_error("manifest.json annotation_versions must not be empty")
    if not class_list:
        report.add_error("manifest.json class_list must not be empty")
    elif class_list[0] != "person":
        report.add_error("manifest.json class_list[0] must be 'person' for the current trainer target")

    dataset_classes = _dataset_class_list(dataset_yaml.get("names"))
    if not dataset_classes:
        report.add_error("dataset.yaml names must be a zero-indexed mapping")
    elif class_list and dataset_classes != class_list:
        report.add_error("dataset.yaml names must match manifest.json class_list")

    split_counts: dict[str, int] = {}
    split_images: list[str] = []
    object_count = 0
    for split_name in ["train", "val", "test"]:
        split_rel = dataset_yaml.get(split_name)
        if split_rel in {None, ""}:
            continue
        split_path = release_root / str(split_rel)
        if not split_path.exists():
            report.add_error(f"dataset.yaml references missing {split_name} split: {split_rel}")
            continue
        split_entries = _read_split_file(split_path)
        split_counts[split_name] = len(split_entries)
        split_images.extend(split_entries)
        for image_rel in split_entries:
            image_path = Path(image_rel)
            resolved_image = image_path if image_path.is_absolute() else release_root / image_path
            if not resolved_image.exists():
                report.add_error(f"missing image referenced by {split_name} split: {image_rel}")
                continue

            label_path = _label_path_for_image(release_root, image_rel)
            if not label_path.exists():
                report.add_error(f"missing label for {split_name} image: {image_rel}")
                continue
            object_count += _validate_yolo_label_file(
                label_path,
                f"label {label_path.relative_to(release_root)}",
                report,
            )

    for split_name, expected_count in counts_by_split.items():
        observed_count = split_counts.get(split_name, 0)
        if expected_count != observed_count:
            report.add_error(
                f"manifest.json counts_by_split.{split_name}={expected_count} "
                f"does not match observed count {observed_count}"
            )

    provenance_records = manifest.get("provenance_records", [])
    provenance_paths = _ensure_string_list(provenance_records, "manifest.json provenance_records", report)
    for relative_path in provenance_paths:
        record_path = release_root / relative_path
        if not record_path.exists():
            report.add_error(f"manifest.json references missing provenance record: {relative_path}")

    report.counts = {
        "train_images": split_counts.get("train", 0),
        "val_images": split_counts.get("val", 0),
        "test_images": split_counts.get("test", 0),
        "split_images": len(split_images),
        "object_count": object_count,
        "provenance_record_files": len(provenance_paths),
        "label_sources": len(counts_by_label_source),
    }
    report.details = {
        "release_id": manifest.get("release_id"),
        "source_package_ids": source_package_ids,
        "annotation_versions": annotation_versions,
        "class_list": class_list,
        "counts_by_label_source": counts_by_label_source,
    }

    report.ok = not report.errors
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate package and curated release contracts.")
    parser.add_argument("--phase1", action="append", default=[], help="Path to a phase 1 package root.")
    parser.add_argument("--phase2", action="append", default=[], help="Path to a phase 2 package root.")
    parser.add_argument("--release", action="append", default=[], help="Path to a curated release root.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.phase1 and not args.phase2 and not args.release:
        parser.error("provide at least one --phase1, --phase2, or --release path")

    reports: list[ValidationReport] = []
    for root in args.phase1:
        reports.append(validate_phase1_package(root))
    for root in args.phase2:
        reports.append(validate_phase2_package(root))
    for root in args.release:
        reports.append(validate_curated_release(root))

    payload: Any
    if len(reports) == 1:
        payload = reports[0].to_dict()
    else:
        payload = [report.to_dict() for report in reports]

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if all(report.ok for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
