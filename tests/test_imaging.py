import fitz
import pytest
from PIL import Image
from src.document_loader import pages, preview
from src.region_selector import normalize_box, pixel_box, crop
from src.template_manager import save, load, delete

def test_pdf_jpeg_png_and_geometry(tmp_path, monkeypatch):
    import src.template_manager as tm
    monkeypatch.setattr(tm, "TEMPLATES", tmp_path)
    original = Image.new("RGB", (400, 200), "white")
    for ext in ("png", "jpg"):
        path = tmp_path / f"form.{ext}"
        original.save(path)
        assert next(pages(path))[1].size == (400, 200)
    pdf = fitz.open()
    pdf.new_page(width=100, height=100)
    pdf.new_page(width=200, height=100)
    path = tmp_path / "form.pdf"
    pdf.save(path)
    assert len(list(pages(path))) == 2
    assert preview(original, 200).size == (200, 100)
    box = normalize_box({"left": 20, "top": 10, "width": 40, "height": 20}, 200, 100)
    assert pixel_box(box, 400, 200) == (40, 20, 120, 60)
    assert crop(original, box).size == (80, 40)
    with pytest.raises(ValueError):
        normalize_box({"left": -1, "top": 0, "width": 40, "height": 20}, 200, 100)
    with pytest.raises(ValueError):
        pixel_box([.8, .2, .2, .3], 400, 200)
    template = {"name": "sample", "fields": [{"name": "Name", "page": 1, "mode": "handwritten", "box": box}]}
    save(template)
    assert load("sample") == template
    delete("sample")
