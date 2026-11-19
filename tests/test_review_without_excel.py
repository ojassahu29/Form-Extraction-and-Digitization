from PIL import Image
from src.manifest_manager import read, write
from src.human_review import correct, flag
from src.ocr_engine import OCREngine

def test_blank_crop_and_persistent_correction(tmp_path):
    crop = tmp_path / "blank.png"
    Image.new("RGB", (100, 30), "white").save(crop)
    assert OCREngine().recognize(crop, "handwritten")[0] == ""
    path = tmp_path / "results.json"
    write(path, [{"image_id": "abc", "prediction": "Alic", "corrected_text": None, "status": "SUCCESS", "review_status": "NOT_REQUIRED", "reason": ""}])
    flag(path, "abc")
    assert read(path)[0]["status"] == "NEEDS_REVIEW"
    correct(path, "abc", "Alice")
    assert read(path)[0]["prediction"] == "Alic"
    assert read(path)[0]["corrected_text"] == "Alice"
    assert read(path)[0]["status"] == "MANUALLY_CORRECTED"
