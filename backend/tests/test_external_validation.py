import csv
import hashlib
from argparse import Namespace
from pathlib import Path

from PIL import Image

from scripts.external_validation_utils import (
    ALLOWED_MAPPING_STATUSES,
    build_run_metadata,
    classification_metrics,
    confidence_statistics,
    duplicate_report,
    percentile,
    read_manifest,
    selective_metrics,
    sha256_file,
    threshold_analysis,
    validate_manifest_rows,
    write_csv,
)
from scripts import evaluate_external_dataset as evaluator
from app.core.config import settings


COLUMNS = [
    "external_image_id", "local_relative_path", "dataset_name", "dataset_version",
    "original_label", "mapped_greenmind_label", "mapping_status", "crop", "source_url",
    "source_dataset", "collection_environment", "plant_id", "field_id", "capture_session_id",
    "device_id", "annotation_confidence", "annotation_source", "sha256", "perceptual_hash",
    "duplicate_group_id", "split", "exclusion_reason",
]


def row(image_id, status="EXACT", mapped="Tomato___Early_blight"):
    return {key: "" for key in COLUMNS} | {
        "external_image_id": image_id,
        "local_relative_path": f"{image_id}.jpg",
        "dataset_name": "synthetic",
        "original_label": "Tomato Early blight leaf",
        "mapped_greenmind_label": mapped,
        "mapping_status": status,
    }


def test_manifest_validation_preserves_statuses_and_rejects_invalid_status():
    rows = validate_manifest_rows([row("exact"), row("ambiguous", "AMBIGUOUS", ""), row("unsupported", "UNSUPPORTED", ""), row("bad", "NOT_ALLOWED", "")])
    assert rows[0]["mapping_status"] == "EXACT"
    assert rows[1]["exclusion_reason"] == ""
    assert rows[2]["exclusion_reason"] == ""
    assert "invalid mapping_status" in rows[3]["exclusion_reason"]
    assert ALLOWED_MAPPING_STATUSES == {"EXACT", "POSSIBLE_BUT_REQUIRES_DOCUMENTED_RULE", "AMBIGUOUS", "UNSUPPORTED"}


def test_read_manifest_reports_missing_schema_columns(tmp_path):
    path = tmp_path / "manifest.csv"
    path.write_text("external_image_id,local_relative_path\na,a.jpg\n", encoding="utf-8")
    rows, missing = read_manifest(path)
    assert rows[0]["external_image_id"] == "a"
    assert "mapping_status" in missing


def test_sha256_and_duplicate_report(tmp_path):
    first = tmp_path / "a.jpg"
    second = tmp_path / "b.jpg"
    first.write_bytes(b"same-bytes")
    second.write_bytes(b"same-bytes")
    digest = sha256_file(first)
    assert digest == hashlib.sha256(b"same-bytes").hexdigest()
    report = duplicate_report([
        {"external_image_id": "a", "sha256": digest, "perceptual_hash": "1111"},
        {"external_image_id": "b", "sha256": digest, "perceptual_hash": "1111"},
        {"external_image_id": "c", "sha256": "other", "perceptual_hash": "0000"},
    ])
    assert {item["duplicate_type"] for item in report if item["external_image_id"] in {"a", "b"}} == {"exact_duplicate", "probable_visual_duplicate_review_required"}
    assert next(item for item in report if item["external_image_id"] == "c")["duplicate_type"] == "unique_or_unhashed"


def test_metrics_and_confidence_threshold_are_explicit():
    metrics = classification_metrics(["a", "a", "b"], ["a", "b", "b"], ["a", "b"])
    assert metrics["accuracy"] == 2 / 3
    assert metrics["per_class"]["a"]["support"] == 2
    stats = confidence_statistics([0.2, 0.6, 0.9])
    assert stats["median"] == 0.6
    assert percentile([0.2, 0.6, 0.9], 50) == 0.6
    selective = selective_metrics([0.2, 0.6, 0.9], [False, True, True], 0.60)
    assert selective["accepted_coverage"] == 2 / 3
    assert selective["accepted_accuracy"] == 1.0
    assert selective["rejected_coverage"] == 1 / 3
    assert threshold_analysis([0.2, 0.6, 0.9], [0.60])[0]["rejection_rate"] == 1 / 3


def test_manifest_writer_and_metadata_keep_unknowns_explicit(tmp_path):
    manifest = tmp_path / "manifest.csv"
    write_csv(manifest, [row("one")], COLUMNS)
    assert manifest.exists()
    metadata = build_run_metadata(
        dataset_name="synthetic",
        dataset_version=None,
        dataset_release_date=None,
        dataset_source_url=None,
        download_date=None,
        license_review_date=None,
        manifest_filename="manifest.csv",
        manifest_sha256=None,
        image_count_before_filtering=1,
        image_count_after_filtering=1,
        excluded_image_count=0,
        model_path="model.pt",
        model_sha256=None,
        class_names_path="class_names.json",
        class_names_sha256=None,
        model_architecture="efficientnet_b0",
        model_input_size=224,
        preprocessing_mean=[0.485, 0.456, 0.406],
        preprocessing_std=[0.229, 0.224, 0.225],
        confidence_threshold=0.60,
        random_seed=None,
        evaluation_script_version="test",
    )
    assert metadata["dataset_version"] is None
    assert metadata["confidence_threshold"] == 0.60
    assert metadata["model_input_size"] == 224


def test_direct_evaluator_includes_exact_only_and_exports_exclusions(tmp_path, monkeypatch):
    image_root = tmp_path / "images"
    image_root.mkdir()
    Image.new("RGB", (12, 12), color=(20, 30, 40)).save(image_root / "exact.jpg")
    Image.new("RGB", (12, 12), color=(50, 60, 70)).save(image_root / "ambiguous.jpg")
    manifest = tmp_path / "manifest.csv"
    write_csv(manifest, [row("exact"), row("ambiguous", "AMBIGUOUS", "")], COLUMNS)

    model_path = tmp_path / "model.pt"
    model_path.write_bytes(b"model")
    class_path = tmp_path / "class_names.json"
    class_path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(settings, "MODEL_PATH", str(model_path))
    monkeypatch.setattr(evaluator.model_loader, "load_model", lambda: None)
    monkeypatch.setattr(evaluator.model_loader, "get_model", lambda: object())
    monkeypatch.setattr(evaluator.model_loader, "get_class_names", lambda: ["Tomato___Early_blight"] * 38)
    monkeypatch.setattr(evaluator.model_loader, "is_fallback_mode", lambda: False)
    monkeypatch.setattr(evaluator, "infer_image", lambda path, model, names, preprocess: ("Tomato___Early_blight", 0.75))

    args = Namespace(
        manifest=str(manifest), image_root=str(image_root), dataset_name="synthetic",
        mode="direct", output_root=str(tmp_path / "reports"), dataset_version=None,
        dataset_release_date=None, dataset_source_url=None, download_date=None,
        license_review_date=None, random_seed=None, model_path=None,
    )
    result = evaluator.evaluate(args)
    assert result["included"] == 1
    assert result["excluded"] == 1
    assert (tmp_path / "reports" / "synthetic" / "excluded_rows.csv").exists()
    metrics = (tmp_path / "reports" / "synthetic" / "metrics.json").read_text(encoding="utf-8")
    assert '"included_images": 1' in metrics


def test_ood_evaluator_reports_rejection_and_confident_known_class_error(tmp_path, monkeypatch):
    image_root = tmp_path / "images"
    image_root.mkdir()
    Image.new("RGB", (12, 12), color=(20, 30, 40)).save(image_root / "ood.jpg")
    manifest = tmp_path / "ood.csv"
    write_csv(manifest, [row("ood", "UNSUPPORTED", "")], COLUMNS)
    model_path = tmp_path / "model.pt"
    model_path.write_bytes(b"model")
    monkeypatch.setattr(settings, "MODEL_PATH", str(model_path))
    monkeypatch.setattr(evaluator.model_loader, "load_model", lambda: None)
    monkeypatch.setattr(evaluator.model_loader, "get_model", lambda: object())
    monkeypatch.setattr(evaluator.model_loader, "get_class_names", lambda: ["Tomato___Early_blight"] * 38)
    monkeypatch.setattr(evaluator.model_loader, "is_fallback_mode", lambda: False)
    monkeypatch.setattr(evaluator, "infer_image", lambda path, model, names, preprocess: ("Tomato___Early_blight", 0.8))
    args = Namespace(
        manifest=str(manifest), image_root=str(image_root), dataset_name="synthetic_ood",
        mode="ood", output_root=str(tmp_path / "reports"), dataset_version=None,
        dataset_release_date=None, dataset_source_url=None, download_date=None,
        license_review_date=None, random_seed=None, model_path=None,
    )
    result = evaluator.evaluate(args)
    assert result["metrics"]["rejection_rate"] == 0.0
    assert result["metrics"]["confident_known_class_error_rate"] == 1.0
    assert result["metrics"]["predicted_class_distribution"]["Tomato___Early_blight"] == 1


def test_high_confidence_wrong_prediction_is_exported_for_review(tmp_path, monkeypatch):
    image_root = tmp_path / "images"
    image_root.mkdir()
    Image.new("RGB", (12, 12), color=(20, 30, 40)).save(image_root / "wrong.jpg")
    manifest = tmp_path / "manifest.csv"
    write_csv(manifest, [row("wrong")], COLUMNS)
    model_path = tmp_path / "model.pt"
    model_path.write_bytes(b"model")
    monkeypatch.setattr(settings, "MODEL_PATH", str(model_path))
    monkeypatch.setattr(evaluator.model_loader, "load_model", lambda: None)
    monkeypatch.setattr(evaluator.model_loader, "get_model", lambda: object())
    monkeypatch.setattr(evaluator.model_loader, "get_class_names", lambda: ["Tomato___Early_blight", "Tomato___Late_blight"] * 19)
    monkeypatch.setattr(evaluator.model_loader, "is_fallback_mode", lambda: False)
    monkeypatch.setattr(evaluator, "infer_image", lambda path, model, names, preprocess: ("Tomato___Late_blight", 0.95))
    args = Namespace(
        manifest=str(manifest), image_root=str(image_root), dataset_name="synthetic_wrong",
        mode="direct", output_root=str(tmp_path / "reports"), dataset_version=None,
        dataset_release_date=None, dataset_source_url=None, download_date=None,
        license_review_date=None, random_seed=None, model_path=None,
    )
    evaluator.evaluate(args)
    failures = (tmp_path / "reports" / "synthetic_wrong" / "failure_cases.csv").read_text(encoding="utf-8")
    assert "High-confidence wrong prediction" in failures
