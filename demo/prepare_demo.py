"""Prepare visible Phase 1 results from the two synthetic sample forms."""

from pathlib import Path

from src.image_extractor import process
from src.template_manager import save
from src.config import IMAGE_BOOK


def main():
    root = Path(__file__).resolve().parent
    template = {
        "name": "sample_layout",
        "reference_width": 1200,
        "reference_height": 800,
        "reference_page": 1,
        "fields": [
            {"name": "Name", "page": 1, "mode": "handwritten", "box": [365/1200, 120/800, 1080/1200, 200/800]},
            {"name": "Roll Number", "page": 1, "mode": "handwritten", "box": [365/1200, 300/800, 1080/1200, 380/800]},
            {"name": "Date", "page": 1, "mode": "handwritten", "box": [365/1200, 480/800, 1080/1200, 560/800]},
        ],
    }
    save(template)
    forms = [root / "sample_form.png", root / "sample_form_2.png"]
    for source, status in process(forms, template):
        print(f"{status}: {source}")
    print(f"Open {IMAGE_BOOK}")


if __name__ == "__main__":
    main()
