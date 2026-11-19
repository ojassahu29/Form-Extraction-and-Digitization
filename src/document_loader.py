from pathlib import Path
import fitz
from PIL import Image, ImageOps

SUPPORTED = {".pdf", ".jpg", ".jpeg", ".png"}

def pages(path, dpi=200):
    path = Path(path)
    if path.suffix.lower() not in SUPPORTED:
        raise ValueError(f"Unsupported form: {path.name}")
    if path.suffix.lower() == ".pdf":
        with fitz.open(path) as pdf:
            for index, page in enumerate(pdf):
                pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
                yield index + 1, Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    else:
        with Image.open(path) as raw:
            yield 1, ImageOps.exif_transpose(raw).convert("RGB").copy()

def preview(image, max_width=900):
    result = image.copy()
    result.thumbnail((max_width, 1400))
    return result
