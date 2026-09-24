import io
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

from app.ml import model_loader
from app.services import xai_service


class _FixedModel(torch.nn.Module):
    def forward(self, tensor):
        logits = torch.zeros((tensor.shape[0], 38), dtype=torch.float32)
        logits[:, 7] = 4.0
        return logits


def _image(size=32):
    return Image.new("RGB", (size, size), color=(70, 150, 80))


def _classes():
    return [f"class_{index}" for index in range(38)]


def test_prediction_callback_returns_exactly_38_probabilities(monkeypatch):
    monkeypatch.setattr(model_loader, "get_model", lambda: _FixedModel())
    monkeypatch.setattr(model_loader, "get_class_names", _classes)
    callback = xai_service._prediction_callback()

    probabilities = callback(np.zeros((2, 32, 32, 3), dtype=np.uint8))

    assert probabilities.shape == (2, 38)
    assert np.isfinite(probabilities).all()
    assert np.all(probabilities >= 0)
    assert np.allclose(probabilities.sum(axis=1), 1.0)


def test_callback_reuses_existing_preprocessing(monkeypatch):
    monkeypatch.setattr(model_loader, "get_model", lambda: _FixedModel())
    monkeypatch.setattr(model_loader, "get_class_names", _classes)
    calls = []

    def fake_preprocess(image):
        calls.append(image.size)
        return torch.zeros((1, 3, 8, 8), dtype=torch.float32)

    monkeypatch.setattr(xai_service, "preprocess_for_model", fake_preprocess)
    callback = xai_service._prediction_callback()
    callback(np.zeros((1, 16, 16, 3), dtype=np.uint8))

    assert calls == [(16, 16)]


def test_class_mapping_and_target_class_are_taken_from_model_loader(monkeypatch):
    classes = _classes()
    monkeypatch.setattr(model_loader, "get_model", lambda: _FixedModel())
    monkeypatch.setattr(model_loader, "get_class_names", lambda: classes)
    monkeypatch.setattr(xai_service.settings, "XAI_LIME_NUM_SAMPLES", 4)

    result = xai_service.explain_image(_image(), classes[7])

    assert result.target_class == classes[7]
    assert result.target_index == 7
    assert result.segments
    assert isinstance(result.segments[0]["segment_id"], int)
    assert isinstance(result.segments[0]["weight"], float)
    assert isinstance(result.segments[0]["supports_prediction"], bool)
    assert result.image_bytes.startswith(b"\x89PNG")


def test_explanation_response_structure(monkeypatch):
    classes = _classes()
    monkeypatch.setattr(model_loader, "get_model", lambda: _FixedModel())
    monkeypatch.setattr(model_loader, "get_class_names", lambda: classes)
    monkeypatch.setattr(xai_service.settings, "XAI_LIME_NUM_SAMPLES", 2)

    result = xai_service.explain_image(_image(), classes[7])
    response_shape = {
        "target_class": result.target_class,
        "segments": result.segments,
        "image_bytes": result.image_bytes,
    }

    assert set(response_shape) == {"target_class", "segments", "image_bytes"}
    assert all(set(segment) == {"segment_id", "weight", "supports_prediction"} for segment in result.segments)


def test_invalid_target_class_is_rejected(monkeypatch):
    monkeypatch.setattr(model_loader, "get_class_names", _classes)
    with pytest.raises(ValueError, match="configured 38-class mapping"):
        xai_service.explain_image(_image(), "not-a-class")


def test_missing_or_unsafe_image_is_handled_safely(tmp_path, monkeypatch):
    monkeypatch.setattr(xai_service.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    with pytest.raises(FileNotFoundError):
        xai_service.load_original_image(str(tmp_path / "uploads" / "missing.jpg"))

    outside = tmp_path / "outside.jpg"
    outside.write_bytes(b"not-an-image")
    with pytest.raises(ValueError, match="outside the secure upload directory"):
        xai_service.load_original_image(str(outside))


def test_lime_failure_is_returned_to_caller(monkeypatch):
    classes = _classes()
    monkeypatch.setattr(model_loader, "get_model", lambda: _FixedModel())
    monkeypatch.setattr(model_loader, "get_class_names", lambda: classes)

    class BrokenExplainer:
        def __init__(self, *args, **kwargs):
            pass

        def explain_instance(self, *args, **kwargs):
            raise RuntimeError("lime failed")

    monkeypatch.setattr("lime.lime_image.LimeImageExplainer", BrokenExplainer)
    with pytest.raises(RuntimeError, match="lime failed"):
        xai_service.explain_image(_image(), classes[0])
