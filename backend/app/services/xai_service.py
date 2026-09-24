"""On-demand LIME explanations for accepted disease predictions."""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw

from app.core.config import settings
from app.ml import model_loader
from app.ml.preprocessing import preprocess_for_model


XAI_DISCLAIMER = (
    "LIME provides a local explanation of image regions that influenced the "
    "model's prediction. Highlighted regions indicate model influence and "
    "should not be interpreted as definitive biological evidence."
)


@dataclass
class ExplanationResult:
    target_class: str
    target_index: int
    segments: list[dict]
    image_bytes: bytes


def _prediction_callback() -> Callable[[np.ndarray], np.ndarray]:
    """Create LIME's batch callback using the existing model and preprocessing."""
    model = model_loader.get_model()
    class_names = model_loader.get_class_names()
    if model is None or len(class_names) != 38:
        raise RuntimeError("The trained 38-class disease model is unavailable")

    import torch

    def predict_batch(images: np.ndarray) -> np.ndarray:
        if images.ndim != 4:
            raise ValueError("LIME must provide a batch of HWC images")

        tensors = torch.cat(
            [preprocess_for_model(Image.fromarray(image.astype(np.uint8), mode="RGB")) for image in images],
            dim=0,
        )
        with torch.no_grad():
            probabilities = torch.softmax(model(tensors), dim=1).cpu().numpy()

        if probabilities.shape != (len(images), len(class_names)):
            raise RuntimeError("Model probabilities do not match the configured class mapping")
        return probabilities

    return predict_batch


def load_original_image(image_path: str) -> Image.Image:
    """Load an uploaded image only when it remains inside the upload directory."""
    path = Path(image_path).resolve()
    upload_dir = Path(settings.UPLOAD_DIR).resolve()
    try:
        path.relative_to(upload_dir)
    except ValueError as exc:
        raise ValueError("Prediction image is outside the secure upload directory") from exc

    if not path.is_file():
        raise FileNotFoundError("Prediction image was not found")

    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return image.convert("RGB")


def _render_overlay(image: Image.Image, explanation, target_index: int) -> bytes:
    """Render positive regions in green and negative regions in red."""
    original = np.asarray(image.convert("RGB")).copy()
    _, mask = explanation.get_image_and_mask(
        label=target_index,
        positive_only=False,
        num_features=settings.XAI_LIME_NUM_FEATURES,
        hide_rest=False,
    )

    overlay = original.astype(np.float32)
    positive = mask > 0
    negative = mask < 0
    overlay[positive] = overlay[positive] * 0.45 + np.array([50, 180, 70], dtype=np.float32) * 0.55
    overlay[negative] = overlay[negative] * 0.45 + np.array([210, 65, 55], dtype=np.float32) * 0.55

    output = Image.fromarray(np.clip(overlay, 0, 255).astype(np.uint8), mode="RGB")
    draw = ImageDraw.Draw(output)
    draw.rectangle((8, 8, 310, 54), fill=(255, 255, 255))
    draw.text((14, 14), "Green: supports  Red: opposes", fill=(20, 20, 20))

    from io import BytesIO
    buffer = BytesIO()
    output.save(buffer, format="PNG")
    return buffer.getvalue()


def explain_image(image: Image.Image, target_class: str) -> ExplanationResult:
    """Generate a conservative local LIME explanation for one known class."""
    class_names = model_loader.get_class_names()
    if len(class_names) != 38 or target_class not in class_names:
        raise ValueError("Target class is not in the configured 38-class mapping")

    target_index = class_names.index(target_class)
    callback = _prediction_callback()

    from lime import lime_image

    image_array = np.asarray(image.convert("RGB"))
    explainer = lime_image.LimeImageExplainer(random_state=0)
    explanation = explainer.explain_instance(
        image_array,
        callback,
        labels=(target_index,),
        top_labels=None,
        hide_color=0,
        num_samples=settings.XAI_LIME_NUM_SAMPLES,
    )

    segments = [
        {
            "segment_id": int(segment_id),
            "weight": round(float(weight), 6),
            "supports_prediction": bool(weight > 0),
        }
        for segment_id, weight in explanation.local_exp[target_index]
    ]
    segments.sort(key=lambda item: abs(item["weight"]), reverse=True)

    return ExplanationResult(
        target_class=target_class,
        target_index=target_index,
        segments=segments,
        image_bytes=_render_overlay(image, explanation, target_index),
    )
