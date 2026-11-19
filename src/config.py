from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
INPUT = DATA / "input"
CROPS = DATA / "crops"
OUTPUT = DATA / "output"
MANIFESTS = DATA / "manifests"
TEMPLATES = ROOT / "templates"
IMAGE_BOOK = OUTPUT / "Image_extract.xlsx"
TEXT_BOOK = OUTPUT / "Text_extraction.xlsx"
MANIFEST = MANIFESTS / "crops.json"
RESULTS = MANIFESTS / "ocr_results.json"

def ensure_dirs():
    for path in (INPUT, CROPS, OUTPUT, MANIFESTS, TEMPLATES):
        path.mkdir(parents=True, exist_ok=True)
