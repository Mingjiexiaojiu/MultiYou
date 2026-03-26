import io
import os

from PIL import Image

MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_TYPES = {"image/jpeg", "image/png"}


def validate_image(file_bytes: bytes, content_type: str) -> None:
    """Raise ValueError for unsupported type or oversized files."""
    if content_type not in ALLOWED_TYPES:
        raise ValueError("Only JPG and PNG images are allowed.")
    if len(file_bytes) > MAX_SIZE_BYTES:
        raise ValueError("Image size must not exceed 5 MB.")


def pixelate_avatar(image_bytes: bytes, output_path: str) -> str:
    """Resize → 512×512, pixelate via 32×32, upscale to 128×128, save PNG."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    img = img.resize((512, 512), Image.LANCZOS)
    small = img.resize((32, 32), Image.NEAREST)
    pixel = small.resize((128, 128), Image.NEAREST)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pixel.save(output_path, format="PNG")
    return output_path
