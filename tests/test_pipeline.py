from pathlib import Path
import fitz
import pytest
from PIL import Image, ImageDraw
from src.document_loader import pages
from src.region_selector import normalize_box, pixel_box, crop
from src.template_manager import save, load, delete
from src.image_extractor import process
from src.manifest_manager import read
from src.excel_manager import validate_workbook
from src.ocr_engine import run
from src.human_review import correct
from src.export_manager import export

def form(path, label):
    im = Image.new("RGB", (400, 200), "white")
    ImageDraw.Draw(im).text((40, 50), label, fill="black")
    im.save(path)

def test_loading_geometry_and_template(tmp_path, monkeypatch):
    import src.template_manager as tm
    monkeypatch.setattr(tm, "TEMPLATES", tmp_path)
    png = tmp_path / "one.png"
    jpg = tmp_path / "one.jpg"
    form(png, "A")
    form(jpg, "A")
    assert next(pages(png))[1].size == (400, 200)
    assert next(pages(jpg))[1].size == (400, 200)
    pdf = fitz.open()
    pdf.new_page(width=100, height=100)
    pdf_path = tmp_path / "one.pdf"
    pdf.save(pdf_path)
    assert len(list(pages(pdf_path))) == 1
    box = normalize_box({"left": 20, "top": 10, "width": 40, "height": 20}, 200, 100)
    assert pixel_box(box, 400, 200) == (40, 20, 120, 60)
    assert crop(Image.new("RGB", (400, 200)), box).size == (80, 40)
    with pytest.raises(ValueError):
        normalize_box({"left": -1, "top": 0, "width": 4, "height": 4}, 200, 100)
    template = {"name": "test", "fields": [{"name": "Name", "page": 1, "mode": "handwritten", "box": box}]}
    save(template)
    assert load("test") == template
    delete("test")

def test_batch_excel_manifest_ocr_review_export(tmp_path):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    form(a, "Alice")
    form(b, "Bob")
    template = {"name": "demo", "fields": [{"name": "Name", "page": 1, "mode": "handwritten", "box": [.05, .15, .8, .5]}]}
    book = tmp_path / "Image_extract.xlsx"
    manifest = tmp_path / "manifest.json"
    crops = tmp_path / "crops"
    assert process([a], template, image_book=book, manifest_path=manifest, crop_dir=crops, input_dir=tmp_path / "input")[0][1] == "PROCESSED"
    assert process([b], template, image_book=book, manifest_path=manifest, crop_dir=crops, input_dir=tmp_path / "input")[0][1] == "PROCESSED"
    assert process([a], template, image_book=book, manifest_path=manifest, crop_dir=crops, input_dir=tmp_path / "input")[0][1] == "SKIPPED_DUPLICATE"
    rows = read(manifest)
    assert len(rows) == 2
    assert validate_workbook(book, rows)
    from openpyxl import load_workbook
    wb = load_workbook(book)
    assert len(wb.active._images) == 2
    assert wb.active["B1"].value == "Name"
    class MockOCR:
        def recognize(self, path, mode):
            if Path(path).name == rows[0]["image_id"] + ".png":
                return "Alic", "mock", "uncertain"
            raise RuntimeError("mock failure")
    result_path = tmp_path / "results.json"
    results = run(rows, book, result_path, engine=MockOCR())
    assert [r["status"] for r in results] == ["NEEDS_REVIEW", "FAILED"]
    assert results[0]["prediction"] == "Alic"
    correct(result_path, rows[0]["image_id"], "Alice")
    out = tmp_path / "Text_extraction.xlsx"
    export(book, rows, read(result_path), out)
    text = load_workbook(out)
    assert text.active["B2"].value == "Alice"
    assert text.active["A3"].value == rows[1]["source_id"]
    assert text["Review_Status"]["D3"].value == "FAILED"

def test_invalid_region_and_missing_page(tmp_path):
    source = tmp_path / "x.png"
    form(source, "X")
    template = {"name": "invalid", "fields": [{"name": "X", "page": 2, "mode": "auto", "box": [.1, .1, .2, .2]}]}
    outcome = process([source], template, image_book=tmp_path / "book.xlsx", manifest_path=tmp_path / "manifest.json", crop_dir=tmp_path / "crops", input_dir=tmp_path / "input")
    assert outcome[0][1].startswith("FAILED:")
