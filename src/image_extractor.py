import hashlib
import json
from pathlib import Path
from .config import INPUT, CROPS, IMAGE_BOOK, MANIFEST, ensure_dirs
from .document_loader import pages
from .region_selector import crop
from .manifest_manager import read, write
from .excel_manager import image_workbook, validate_workbook

def import_form(path, input_dir=INPUT):
    ensure_dirs()
    input_dir = Path(input_dir)
    input_dir.mkdir(parents=True, exist_ok=True)
    source = Path(path)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    if source.resolve().parent == input_dir.resolve():
        return source, digest
    target = input_dir / f"{digest}_{source.name}"
    if not target.exists():
        target.write_bytes(source.read_bytes())
    return target, digest

def process(paths, template, force=False, image_book=IMAGE_BOOK, manifest_path=MANIFEST, crop_dir=CROPS, input_dir=INPUT):
    """Persist crops, manifest and workbook. Return one status per source."""
    ensure_dirs()
    crop_dir = Path(crop_dir)
    crop_dir.mkdir(parents=True, exist_ok=True)
    records = read(manifest_path)
    outcomes = []
    for path in paths:
        try:
            saved, digest = import_form(path, input_dir)
            source_id = f"{digest}_{Path(path).name}"
            prior = [r for r in records if r["source_id"] == source_id]
            if prior:
                if not force:
                    outcomes.append((source_id, "SKIPPED_DUPLICATE"))
                    continue
            retained = [r for r in records if r["source_id"] != source_id] if prior else records
            page_images = dict(pages(saved))
            row = prior[0]["excel_row"] if prior else max((r["excel_row"] for r in records), default=1) + 1
            pending = []
            for field in template["fields"]:
                page = int(field["page"])
                if page not in page_images:
                    raise ValueError(f"Missing PDF page {page} for {field['name']}")
                picture = crop(page_images[page], field["box"])
                image_id = hashlib.sha256(f"{source_id}|{template['name']}|{json.dumps(field, sort_keys=True)}".encode()).hexdigest()[:20]
                dest = crop_dir / f"{image_id}.png"
                picture.save(dest)
                pending.append({"source_id": source_id, "source_path": str(saved), "template_id": template["name"], "excel_row": row, "excel_column": "", "field": field["name"], "page": page, "mode": field["mode"], "crop_path": str(dest), "image_id": image_id})
            candidate = retained + pending
            image_workbook(image_book, candidate)
            validate_workbook(image_book, candidate)
            write(manifest_path, candidate)
            records = candidate
            outcomes.append((source_id, "PROCESSED"))
        except Exception as exc:
            outcomes.append((str(path), f"FAILED: {exc}"))
    return outcomes
