from pathlib import Path
from PIL import Image, ImageOps
import numpy as np

class OCREngine:
    def __init__(self, handwriting_model="microsoft/trocr-base-handwritten"):
        self.handwriting_model = handwriting_model
        self._processor = self._model = self._device = None

    def _load_handwriting(self):
        if self._model is None:
            import torch
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._processor = TrOCRProcessor.from_pretrained(self.handwriting_model)
            self._model = VisionEncoderDecoderModel.from_pretrained(self.handwriting_model).to(self._device)
            self._model.eval()

    def recognize(self, image_path, mode):
        with Image.open(image_path) as raw:
            image = ImageOps.exif_transpose(raw).convert("RGB")
            if min(image.size) < 4:
                raise ValueError("Crop too small to read")
            arr = np.asarray(image.convert("L"))
            if arr.std() < 3:
                return "", "unreadable", "blank or nearly uniform crop"
            # A line recognizer cannot reliably decode multiple separated baselines.
            foreground = arr < min(210, float(np.median(arr)) - 20)
            occupied = foreground.mean(axis=1) > .015
            runs = []
            start = None
            for i, active in enumerate(occupied):
                if active and start is None:
                    start = i
                elif not active and start is not None:
                    if i - start >= 3:
                        runs.append((start, i))
                    start = None
            if start is not None and len(occupied) - start >= 3:
                runs.append((start, len(occupied)))
            multiline = len(runs) > 1 and any(runs[i+1][0] - runs[i][1] > max(4, image.height * .03) for i in range(len(runs)-1))
            # Auto uses handwriting because this prototype has no type classifier.
            if mode in ("handwritten", "auto"):
                self._load_handwriting()
                import torch
                pixels = self._processor(images=image, return_tensors="pt").pixel_values.to(self._device)
                with torch.no_grad():
                    ids = self._model.generate(pixels, max_new_tokens=128)
                value = self._processor.batch_decode(ids, skip_special_tokens=True)[0].strip()
                return value, self.handwriting_model, "Possible multiline crop; verify manually" if multiline else ("verify auto mode manually" if mode == "auto" else "")
            if mode == "printed":
                from .printed_ocr import configure_tesseract
                pytesseract = configure_tesseract()
                value = pytesseract.image_to_string(image, lang="eng", config="--psm 7").strip()
                return value, "tesseract-psm7", "Possible multiline crop; verify manually" if multiline else ""
            raise ValueError(f"Unknown mode {mode}")

def run(manifest, image_book, results_path, engine=None, progress=None):
    from .excel_manager import validate_workbook
    from .manifest_manager import read, write
    validate_workbook(image_book, manifest)
    engine = engine or OCREngine()
    previous = {r["image_id"]: r for r in read(results_path)}
    output = []
    for number, item in enumerate(manifest, 1):
        existing = previous.get(item["image_id"])
        if existing and existing["status"] == "MANUALLY_CORRECTED":
            output.append(existing)
            if progress:
                progress(number, len(manifest))
            continue
        result = {"image_id": item["image_id"], "source_id": item["source_id"], "field": item["field"], "excel_row": item["excel_row"], "excel_column": item["excel_column"], "crop_path": item["crop_path"], "prediction": "", "corrected_text": None, "model": "", "status": "FAILED", "review_status": "PENDING", "reason": "", "error": ""}
        try:
            value, model, reason = engine.recognize(item["crop_path"], item["mode"])
            result.update(prediction=value, model=model, reason=reason)
            result["status"] = "NEEDS_REVIEW" if not value or reason else "SUCCESS"
            if not value:
                result["reason"] = reason or "Empty OCR prediction"
            if result["status"] == "SUCCESS":
                result["review_status"] = "NOT_REQUIRED"
        except Exception as exc:
            result.update(error=str(exc), reason="OCR error", status="FAILED")
        output.append(result)
        write(results_path, output + [r for r in read(results_path) if r["image_id"] not in {x["image_id"] for x in output}])
        if progress:
            progress(number, len(manifest))
    return output
