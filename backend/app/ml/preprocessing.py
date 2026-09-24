"""
Image validation and preprocessing for the disease-detection pipeline.
"""
import io
from PIL import Image, UnidentifiedImageError

from app.core.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


class ImageValidationError(Exception):
    pass


def validate_image(filename: str, content_type: str, size_bytes: int) -> None:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS or content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise ImageValidationError("Only JPG, JPEG, and PNG images are supported.")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise ImageValidationError(f"Image exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB size limit.")


def load_and_verify_image(raw_bytes: bytes) -> Image.Image:
    """Opens the image and confirms it's a genuine, decodable image (not a renamed non-image file)."""
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img.verify()  # verify() checks integrity but invalidates the object for further use
        img = Image.open(io.BytesIO(raw_bytes))  # re-open for actual use
        return img.convert("RGB")
    except UnidentifiedImageError:
        raise ImageValidationError("The uploaded file is not a valid image.")
    except Exception:
        raise ImageValidationError("Could not process the uploaded image.")


def preprocess_for_model(img: Image.Image):
    """
    Resize + normalize for model input. Returns a torch tensor if torch is
    available; callers in fallback mode never reach this.
    """
    import torchvision.transforms as T

    size = settings.MODEL_INPUT_SIZE
    transform = T.Compose([
        T.Resize((size, size)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),  # ImageNet stats
    ])
    return transform(img).unsqueeze(0)  # add batch dimension
