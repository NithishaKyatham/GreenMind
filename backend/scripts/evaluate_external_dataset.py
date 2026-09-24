"""Standalone offline evaluator for authorized GreenMind external manifests.

Run from the backend directory. It never calls the production API and never
changes model files, class mappings, preprocessing, or production settings.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.ml import model_loader
from app.ml.preprocessing import preprocess_for_model
try:
    from .external_validation_utils import (
        ALLOWED_MAPPING_STATUSES,
        build_run_metadata,
        classification_metrics,
        confidence_statistics,
        image_path_for_row,
        load_class_names,
        read_manifest,
        selective_metrics,
        sha256_file,
        threshold_analysis,
        validate_manifest_rows,
        write_csv,
        infer_image,
    )
except ImportError:
    from external_validation_utils import (
    ALLOWED_MAPPING_STATUSES,
    build_run_metadata,
    classification_metrics,
    confidence_statistics,
    image_path_for_row,
    load_class_names,
    read_manifest,
    selective_metrics,
    sha256_file,
    threshold_analysis,
    validate_manifest_rows,
    write_csv,
    infer_image,
    )

EVALUATION_SCRIPT_VERSION = "1.0.0"
FAILURE_FIELDS = [
    "image_id", "dataset", "original_label", "mapped_label", "predicted_class", "confidence",
    "accepted", "correct", "failure_category", "condition_subset", "source_url", "sha256",
    "perceptual_hash", "reviewer", "review_notes",
]
RESULT_FIELDS = [
    "image_id", "dataset", "original_label", "mapped_label", "predicted_class", "confidence",
    "correct", "accepted_at_0_60", "source_url", "sha256", "perceptual_hash", "condition_subset",
]


def _json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def _base_output(args: argparse.Namespace, dataset_name: str) -> Path:
    return Path(args.output_root) / dataset_name


def _condition(row: dict[str, str]) -> str:
    return row.get("condition_subset", "") or row.get("collection_environment", "")


def _failure_category(mode: str, row: dict[str, str], predicted: str, confidence: float, correct: bool, threshold: float) -> str:
    if mode == "ood" and confidence >= threshold:
        return "OOD confident prediction"
    if correct and confidence < threshold:
        return "Low-confidence correct prediction"
    if not correct and confidence >= 0.90:
        return "High-confidence wrong prediction"
    if not correct and confidence < threshold:
        return "Low-confidence wrong prediction"
    return "UNREVIEWED"


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.manifest).resolve()
    rows, missing = read_manifest(manifest_path)
    if missing:
        raise ValueError(f"Manifest is missing columns: {', '.join(missing)}")
    rows = validate_manifest_rows(rows, args.mode)
    output_dir = _base_output(args, args.dataset_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "plots").mkdir(exist_ok=True)

    model_loader.load_model()
    model = model_loader.get_model()
    class_names = model_loader.get_class_names()
    if model is None or model_loader.is_fallback_mode():
        raise RuntimeError("A real trained GreenMind model is required for external evaluation")
    if len(class_names) != 38:
        raise RuntimeError(f"Expected 38 model classes, found {len(class_names)}")
    if args.model_path and Path(args.model_path).resolve() != Path(settings.MODEL_PATH).resolve():
        raise ValueError("External evaluation uses the configured existing model path")

    results = []
    failures = []
    exclusions = []
    labels = []
    predictions = []
    confidences = []
    correct_values = []
    status_counts = Counter(row.get("mapping_status", "") for row in rows)
    before_count = len(rows)

    for row in rows:
        if row.get("_row_error"):
            exclusions.append(row)
            continue
        if args.mode == "direct" and row.get("mapping_status") != "EXACT":
            row["exclusion_reason"] = row.get("exclusion_reason") or "mapping_status_is_not_EXACT"
            exclusions.append(row)
            continue
        try:
            image_path = image_path_for_row(row, args.image_root)
            if not image_path.is_file():
                raise FileNotFoundError(str(image_path))
            predicted, confidence = infer_image(image_path, model, class_names, preprocess_for_model)
        except (OSError, ValueError) as exc:
            row["exclusion_reason"] = row.get("exclusion_reason") or f"image_unavailable_or_invalid: {exc}"
            exclusions.append(row)
            continue

        mapped = row.get("mapped_greenmind_label", "")
        correct = args.mode == "direct" and predicted == mapped
        accepted = confidence >= settings.CONFIDENCE_THRESHOLD
        confidences.append(confidence)
        correct_values.append(correct)
        if args.mode == "ood":
            predictions.append(predicted)
        if args.mode == "direct":
            labels.append(mapped)
            predictions.append(predicted)
        result = {
            "image_id": row.get("external_image_id", ""),
            "dataset": row.get("dataset_name", args.dataset_name),
            "original_label": row.get("original_label", ""),
            "mapped_label": mapped,
            "predicted_class": predicted,
            "confidence": confidence,
            "correct": correct if args.mode == "direct" else "",
            "accepted_at_0_60": accepted,
            "source_url": row.get("source_url", ""),
            "sha256": row.get("sha256", ""),
            "perceptual_hash": row.get("perceptual_hash", ""),
            "condition_subset": _condition(row),
        }
        results.append(result)
        category = _failure_category(args.mode, row, predicted, confidence, correct, settings.CONFIDENCE_THRESHOLD)
        if args.mode == "ood" or not correct or (correct and not accepted):
            failures.append({
                "image_id": result["image_id"], "dataset": result["dataset"], "original_label": result["original_label"],
                "mapped_label": result["mapped_label"], "predicted_class": predicted, "confidence": confidence,
                "accepted": accepted, "correct": correct if args.mode == "direct" else "", "failure_category": category,
                "condition_subset": result["condition_subset"], "source_url": result["source_url"], "sha256": result["sha256"],
                "perceptual_hash": result["perceptual_hash"], "reviewer": "", "review_notes": "",
            })

    included_count = len(results)
    metrics: dict[str, Any]
    if args.mode == "direct":
        represented = sorted(set(labels))
        metrics = classification_metrics(labels, predictions, represented)
        metrics.update({
            "mode": "direct",
            "total_images": before_count,
            "included_images": included_count,
            "excluded_images": len(exclusions),
            "represented_classes": represented,
            "images_per_class": dict(Counter(labels)),
            "mapping_status_counts": dict(status_counts),
            "selective_metrics": selective_metrics(confidences, correct_values, settings.CONFIDENCE_THRESHOLD),
        })
        write_csv(output_dir / "per_class_metrics.csv", [{"class_name": name, **values} for name, values in metrics["per_class"].items()], ["class_name", "precision", "recall", "f1", "support"])
        _json_write(output_dir / "confusion_matrix.json", metrics["confusion_matrix"])
    else:
        accepted = sum(value >= settings.CONFIDENCE_THRESHOLD for value in confidences)
        metrics = {
            "mode": "ood",
            "total_images": before_count,
            "included_images": included_count,
            "excluded_images": len(exclusions),
            "mapping_status_counts": dict(status_counts),
            "rejection_rate": (included_count - accepted) / included_count if included_count else None,
            "confident_known_class_error_rate": accepted / included_count if included_count else None,
            "predicted_class_distribution": dict(Counter(predictions)),
            "threshold_analysis": threshold_analysis(confidences, [0.40, 0.50, 0.60, 0.70, 0.80, 0.90]),
        }

    confidence_data = confidence_statistics(confidences)
    if args.mode == "direct":
        confidence_data["correct_confidence"] = confidence_statistics([value for value, ok in zip(confidences, correct_values) if ok])
        confidence_data["incorrect_confidence"] = confidence_statistics([value for value, ok in zip(confidences, correct_values) if not ok])
    confidence_data["percentage_below_0_60"] = (sum(value < settings.CONFIDENCE_THRESHOLD for value in confidences) / len(confidences) * 100) if confidences else None
    _json_write(output_dir / "confidence_statistics.json", confidence_data)
    write_csv(output_dir / "manifest_snapshot.csv", rows, sorted(set().union(*(row.keys() for row in rows))) if rows else [])
    write_csv(output_dir / "failure_cases.csv", failures, FAILURE_FIELDS)
    _json_write(output_dir / "metrics.json", metrics)

    class_path = Path(settings.MODEL_PATH).resolve().parent / "class_names.json"
    metadata = build_run_metadata(
        dataset_name=args.dataset_name,
        dataset_version=args.dataset_version,
        dataset_release_date=args.dataset_release_date,
        dataset_source_url=args.dataset_source_url,
        download_date=args.download_date,
        license_review_date=args.license_review_date,
        manifest_filename=manifest_path.name,
        manifest_sha256=sha256_file(manifest_path),
        image_count_before_filtering=before_count,
        image_count_after_filtering=included_count,
        excluded_image_count=len(exclusions),
        model_path=str(Path(settings.MODEL_PATH).resolve()),
        model_sha256=sha256_file(settings.MODEL_PATH) if Path(settings.MODEL_PATH).is_file() else None,
        class_names_path=str(class_path),
        class_names_sha256=sha256_file(class_path) if class_path.is_file() else None,
        model_architecture=settings.MODEL_ARCHITECTURE,
        model_input_size=settings.MODEL_INPUT_SIZE,
        preprocessing_mean=[0.485, 0.456, 0.406],
        preprocessing_std=[0.229, 0.224, 0.225],
        confidence_threshold=settings.CONFIDENCE_THRESHOLD,
        random_seed=args.random_seed,
        evaluation_script_version=EVALUATION_SCRIPT_VERSION,
    )
    _json_write(output_dir / "run_metadata.json", metadata)
    if exclusions:
        write_csv(output_dir / "excluded_rows.csv", exclusions, sorted(set().union(*(row.keys() for row in exclusions))))
    return {"output_dir": str(output_dir), "included": included_count, "excluded": len(exclusions), "metrics": metrics}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--mode", choices=["direct", "ood"], required=True)
    parser.add_argument("--output-root", default="../reports/external_validation")
    parser.add_argument("--dataset-version", default=None)
    parser.add_argument("--dataset-release-date", default=None)
    parser.add_argument("--dataset-source-url", default=None)
    parser.add_argument("--download-date", default=None)
    parser.add_argument("--license-review-date", default=None)
    parser.add_argument("--random-seed", type=int, default=None)
    parser.add_argument("--model-path", default=None)
    args = parser.parse_args()
    result = evaluate(args)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
