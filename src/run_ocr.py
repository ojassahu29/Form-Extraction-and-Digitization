import argparse
from .config import IMAGE_BOOK, TEXT_BOOK, MANIFEST, RESULTS
from .manifest_manager import read
from .ocr_engine import run
from .export_manager import export

def main():
    parser = argparse.ArgumentParser(description="Run Phase 2 on persisted Image_extract.xlsx and crop manifest")
    parser.add_argument("--image-book", default=IMAGE_BOOK)
    parser.add_argument("--manifest", default=MANIFEST)
    parser.add_argument("--results", default=RESULTS)
    parser.add_argument("--output", default=TEXT_BOOK)
    args = parser.parse_args()
    records = read(args.manifest)
    if not records:
        parser.error("No Phase 1 crop manifest found")
    results = run(records, args.image_book, args.results, progress=lambda n, total: print(f"OCR {n}/{total}", flush=True))
    print(export(args.image_book, records, results, args.output))

if __name__ == "__main__":
    main()
