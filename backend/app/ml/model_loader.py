"""
Loads the trained crop-disease model at application startup.

If no trained model file exists, the app runs in DEVELOPMENT FALLBACK mode:
the /api/disease/predict endpoint still works end-to-end (so the rest of
the app is fully testable), but every response is clearly flagged
is_fallback_prediction=True and the confidence/disease values are drawn
from a small deterministic placeholder — never presented as real AI output.
"""
import json
import logging
import os
from typing import List, Optional

from app.core.config import settings

logger = logging.getLogger("greenmind.ml")

_model = None
_class_names: List[str] = []
_is_fallback = True


def _load_class_names() -> List[str]:
    class_names_path = os.path.join(os.path.dirname(settings.MODEL_PATH), "class_names.json")
    if os.path.exists(class_names_path):
        with open(class_names_path) as f:
            return json.load(f)
    # Fallback class list purely so the API has something structurally valid
    # to return in dev mode. Replace by training on a real dataset
    # (see ml/DATASET_SETUP.md) which generates the real class_names.json.
    return [
        "Tomato___healthy",
        "Tomato___Early_blight",
        "Tomato___Late_blight",
        "Potato___healthy",
        "Potato___Late_blight",
    ]


def load_model():
    """Called once at startup (app/main.py). Idempotent."""
    global _model, _class_names, _is_fallback

    _class_names = _load_class_names()

    if not os.path.exists(settings.MODEL_PATH):
        _is_fallback = True
        _model = None
        logger.warning("model_loader: no trained model at %s — fallback mode active", settings.MODEL_PATH)
        return

    try:
        import torch
        import torchvision.models as tvm

        if settings.MODEL_ARCHITECTURE == "efficientnet_b0":
            model = tvm.efficientnet_b0(weights=None)
            model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, len(_class_names))
        elif settings.MODEL_ARCHITECTURE == "mobilenet_v3":
            model = tvm.mobilenet_v3_small(weights=None)
            model.classifier[3] = torch.nn.Linear(model.classifier[3].in_features, len(_class_names))
        else:
            model = tvm.resnet18(weights=None)
            model.fc = torch.nn.Linear(model.fc.in_features, len(_class_names))

        state_dict = torch.load(settings.MODEL_PATH, map_location="cpu")
        model.load_state_dict(state_dict)
        model.eval()

        _model = model
        _is_fallback = False
        logger.info("model_loader: loaded %s from %s (%d classes)",
                    settings.MODEL_ARCHITECTURE, settings.MODEL_PATH, len(_class_names))
    except Exception:
        logger.exception("model_loader: failed to load trained model — falling back to dev mode")
        _model = None
        _is_fallback = True


def get_model():
    return _model


def get_class_names() -> List[str]:
    return _class_names


def is_fallback_mode() -> bool:
    return _is_fallback
