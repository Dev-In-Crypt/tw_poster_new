import tempfile
import os
from PIL import Image


def compress_image(path: str, max_width: int = 1280, quality: int = 82) -> str:
    """Compress and resize image to JPEG for faster Telegram upload."""
    img = Image.open(path)

    # Resize if wider than max_width
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    # Convert to RGB (PNG might be RGBA)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    fd, out_path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    img.save(out_path, "JPEG", quality=quality, optimize=True)
    return out_path
