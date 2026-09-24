"""Offline utilities for GreenMind external validation.

This module is deliberately separate from the production API. It preserves
source labels, accepts only manifest-declared mappings, and never invents
external taxonomy or condition annotations.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np
from PIL import Image

ALLOWED_MAPPING_STATUSES = {
    "EXACT",
    "POSSIBLE_BUT_REQUIRES_DOCUMENTED_RULE",
    "AMBIGUOUS",
    "UNSUPPORTED",
}
REQUIRED_MANIFEST_COLUMNS = {
    "external_image_id",
    "local_relative_path",
    "dataset_name",
    "dataset_version",
    "original_label",
    "mapped_greenmind_label",
    "mapping_status",
    "crop",
    "source_url",
    "source_dataset",
    "collection_environment",
    "plant_id",
    "field_id",
    "capture_session_id",
    "device_id",
    "annotation_confidence",
    "annotation_source",
    "sha256",
    "perceptual_hash",
    "duplicate_group_id",
    "split",
    "exclusion_reason",
}


def read_manifest(path: str | Path) -> tuple[list[dict[str, str]], list[str]]:
    manifest_path = Path(path)
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        missing = sorted(REQUIRED_MANIFEST_COLUMNS - set(fields))
        rows = [{key: (value or "").strip() for key, value in row.items()} for row in reader]
    return rows, missing


def write_csv(path: str | Path, rows: Iterable[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in rows)


def validate_manifest_rows(rows: Sequence[Mapping[str, str]], mode: str = "direct") -> list[dict[str, str]]:
    if mode not in {"direct", "ood"}:
        raise ValueError("mode must be 'direct' or 'ood'")
    validated = []
    for index, raw in enumerate(rows, start=2):
        row = {key: str(raw.get(key, "") or "").strip() for key in REQUIRED_MANIFEST_COLUMNS}
        errors = []
        if not row["external_image_id"]:
            errors.append("missing external_image_id")
        if not row["local_relative_path"]:
            errors.append("missing local_relative_path")
        if not row["original_label"]:
            errors.append("missing original_label")
        if row["mapping_status"] not in ALLOWED_MAPPING_STATUSES:
            errors.append("invalid mapping_status")
        if mode == "direct" and row["mapping_status"] == "EXACT" and not row["mapped_greenmind_label"]:
            errors.append("EXACT row missing mapped_greenmind_label")
        if errors:
            row["exclusion_reason"] = "; ".join(errors)
            row["_row_error"] = f"manifest row {index}: {row['exclusion_reason']}"
        validated.append(row)
    return validated


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def average_hash(path: str | Path, hash_size: int = 8) -> str:
    """Return an aHash; matching hashes are candidates for manual review only."""
    with Image.open(path) as image:
        grayscale = image.convert("L").resize((hash_size, hash_size))
        values = np.asarray(grayscale, dtype=np.float32)
    threshold = float(values.mean())
    bits = values >= threshold
    return "".join("1" if value else "0" for value in bits.flatten())


def duplicate_report(rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    exact: dict[str, list[str]] = {}
    perceptual: dict[str, list[str]] = {}
    for row in rows:
        image_id = row.get("external_image_id", "")
        if row.get("sha256"):
            exact.setdefault(row["sha256"], []).append(image_id)
        if row.get("perceptual_hash"):
            perceptual.setdefault(row["perceptual_hash"], []).append(image_id)

    report = []
    ids = {image_id for group in exact.values() if len(group) > 1 for image_id in group}
    for image_id in sorted(ids):
        report.append({"external_image_id": image_id, "duplicate_type": "exact_duplicate"})
    for group in perceptual.values():
        if len(group) > 1:
            for image_id in group:
                report.append({"external_image_id": image_id, "duplicate_type": "probable_visual_duplicate_review_required"})
    known = {item["external_image_id"] for item in report}
    for row in rows:
        if row.get("external_image_id") not in known:
            report.append({"external_image_id": row.get("external_image_id", ""), "duplicate_type": "unique_or_unhashed"})
    return report


def percentile(values: Sequence[float], fraction: float) -> float | None:
    return float(np.percentile(np.asarray(values, dtype=float), fraction)) if values else None


def confidence_statistics(values: Sequence[float]) -> dict[str, Any]:
    numeric = [float(value) for value in values]
    if not numeric:
        return {"count": 0, "mean": None, "median": None, "std": None, "minimum": None, "maximum": None, "quantiles": {}}
    return {
        "count": len(numeric),
        "mean": float(statistics.mean(numeric)),
        "median": float(statistics.median(numeric)),
        "std": float(statistics.pstdev(numeric)),
        "minimum": min(numeric),
        "maximum": max(numeric),
        "quantiles": {str(q): percentile(numeric, q) for q in (5, 25, 50, 75, 95)},
    }


def _safe_division(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def classification_metrics(labels: Sequence[str], predictions: Sequence[str], class_names: Sequence[str]) -> dict[str, Any]:
    matrix = {actual: {predicted: 0 for predicted in class_names} for actual in class_names}
    for actual, predicted in zip(labels, predictions):
        if actual in matrix and predicted in matrix[actual]:
            matrix[actual][predicted] += 1

    per_class = {}
    supports = []
    for name in class_names:
        tp = matrix[name][name]
        fp = sum(matrix[actual][name] for actual in class_names if actual != name)
        fn = sum(matrix[name][predicted] for predicted in class_names if predicted != name)
        support = sum(matrix[name].values())
        precision = _safe_division(tp, tp + fp)
        recall = _safe_division(tp, tp + fn)
        f1 = _safe_division(2 * precision * recall, precision + recall)
        per_class[name] = {"precision": precision, "recall": recall, "f1": f1, "support": support}
        supports.append(support)

    total = len(labels)
    accuracy = _safe_division(sum(actual == predicted for actual, predicted in zip(labels, predictions)), total)
    macro_precision = statistics.mean(item["precision"] for item in per_class.values()) if per_class else 0.0
    macro_recall = statistics.mean(item["recall"] for item in per_class.values()) if per_class else 0.0
    macro_f1 = statistics.mean(item["f1"] for item in per_class.values()) if per_class else 0.0
    weighted_f1 = _safe_division(sum(item["f1"] * item["support"] for item in per_class.values()), sum(supports))
    return {
        "accuracy": accuracy,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "per_class": per_class,
        "confusion_matrix": matrix,
    }


def selective_metrics(confidences: Sequence[float], correct: Sequence[bool], threshold: float = 0.60) -> dict[str, float | None]:
    accepted = [index for index, confidence in enumerate(confidences) if confidence >= threshold]
    rejected = [index for index, confidence in enumerate(confidences) if confidence < threshold]
    return {
        "threshold": threshold,
        "accepted_coverage": _safe_division(len(accepted), len(confidences)),
        "accepted_accuracy": _safe_division(sum(bool(correct[index]) for index in accepted), len(accepted)) if accepted else None,
        "rejected_coverage": _safe_division(len(rejected), len(confidences)),
        "accuracy_all": _safe_division(sum(bool(value) for value in correct), len(correct)),
    }


def threshold_analysis(confidences: Sequence[float], thresholds: Sequence[float]) -> list[dict[str, float]]:
    return [{"threshold": float(threshold), "rejection_rate": _safe_division(sum(value < threshold for value in confidences), len(confidences)), "acceptance_rate": _safe_division(sum(value >= threshold for value in confidences), len(confidences))} for threshold in thresholds]


def package_versions() -> dict[str, str | None]:
    versions = {"python_version": platform.python_version(), "torch_version": None, "torchvision_version": None, "Pillow_version": None, "scikit_learn_version": None}
    try:
        import torch
        versions["torch_version"] = torch.__version__
    except ImportError:
        pass
    try:
        import torchvision
        versions["torchvision_version"] = torchvision.__version__
    except ImportError:
        pass
    try:
        versions["Pillow_version"] = Image.__version__
    except AttributeError:
        pass
    try:
        import sklearn
        versions["scikit_learn_version"] = sklearn.__version__
    except ImportError:
        pass
    return versions


def build_run_metadata(*, dataset_name: str | None, dataset_version: str | None, dataset_release_date: str | None, dataset_source_url: str | None, download_date: str | None, license_review_date: str | None, manifest_filename: str, manifest_sha256: str | None, image_count_before_filtering: int, image_count_after_filtering: int, excluded_image_count: int, model_path: str, model_sha256: str | None, class_names_path: str, class_names_sha256: str | None, model_architecture: str, model_input_size: int, preprocessing_mean: Sequence[float], preprocessing_std: Sequence[float], confidence_threshold: float, random_seed: int | None, evaluation_script_version: str) -> dict[str, Any]:
    metadata = {
        "dataset_name": dataset_name,
        "dataset_version": dataset_version,
        "dataset_release_date": dataset_release_date,
        "dataset_source_url": dataset_source_url,
        "download_date": download_date,
        "license_review_date": license_review_date,
        "manifest_filename": manifest_filename,
        "manifest_sha256": manifest_sha256,
        "image_count_before_filtering": image_count_before_filtering,
        "image_count_after_filtering": image_count_after_filtering,
        "excluded_image_count": excluded_image_count,
        "model_path": model_path,
        "model_sha256": model_sha256,
        "class_names_path": class_names_path,
        "class_names_sha256": class_names_sha256,
        "model_architecture": model_architecture,
        "model_input_size": model_input_size,
        "preprocessing_mean": list(preprocessing_mean),
        "preprocessing_std": list(preprocessing_std),
        "confidence_threshold": confidence_threshold,
        "random_seed": random_seed,
        "evaluation_script_version": evaluation_script_version,
        "experiment_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    metadata.update(package_versions())
    return metadata


def load_class_names(path: str | Path) -> list[str]:
    with Path(path).open("r", encoding="utf-8") as handle:
        names = json.load(handle)
    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        raise ValueError("class_names.json must contain a JSON list of strings")
    return names


def image_path_for_row(row: Mapping[str, str], image_root: str | Path) -> Path:
    path = (Path(image_root) / row["local_relative_path"]).resolve()
    root = Path(image_root).resolve()
    path.relative_to(root)
    return path


def infer_image(image_path: Path, model: Any, class_names: Sequence[str], preprocess: Callable) -> tuple[str, float]:
    import torch
    with Image.open(image_path) as source:
        image = source.convert("RGB")
    tensor = preprocess(image)
    with torch.no_grad():
        probabilities = torch.softmax(model(tensor), dim=1)[0]
    index = int(torch.argmax(probabilities).item())
    return class_names[index], float(probabilities[index].item())
