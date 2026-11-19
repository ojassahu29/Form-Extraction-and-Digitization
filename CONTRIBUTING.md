# Development guide

## Local setup

Clone the repository and install [requirements.txt](requirements.txt) into a Python 3.10–3.12 virtual environment. Launch `app.py` with Streamlit as described in the README. Current verification was performed on Windows with Python 3.12; Linux/macOS commands are provided but have not been exercised here.

No account keys or hosted OCR API are required. Pretrained TrOCR weights download from Hugging Face on first use. Tesseract is a separate system dependency for printed fields.

## Code map

| Module | Responsibility |
|---|---|
| `app.py` | Navigation, form selection, OCR/review/export screens |
| `src/document_loader.py` | PDF rendering, raster loading and previews |
| `src/canvas.py`, `src/editor_ui.py` | Interactive selection and field controls |
| `src/editor_state.py`, `src/form_regions.py` | Draft recovery and per-form regions |
| `src/template_manager.py`, `src/template_preview.py` | Optional reusable layouts and previews |
| `src/image_extractor.py` | Persistent source/crop extraction and batch flow |
| `src/excel_manager.py`, `src/manifest_manager.py` | Embedded images and mapping validation |
| `src/ocr_engine.py`, `src/printed_ocr.py` | Lazy TrOCR loading, Tesseract discovery, result states |
| `src/human_review.py` | Original prediction and separate persisted correction |
| `src/export_manager.py` | Text workbook, review status and export freshness |
| `src/run_ocr.py` | Independent recognition CLI |

Paths are centralized in `src/config.py`. Theme configuration is in `.streamlit/config.toml`. `PRODUCT.md` and `DESIGN.md` document workflow constraints and the current palette.

## Run tests

```powershell
python run_tests.py
```

The runner selects the repository's virtual environment when available. It creates a unique temporary directory, disables pytest caching and removes successful-run artifacts. Failed-run directories remain for diagnosis.

The current suite has 13 passing tests covering loading, cropping, templates, embedded Excel images, append/deduplication, manifest consistency, mocked OCR failure, manual corrections, export freshness, draft undo, layout recovery, executable discovery and a Streamlit UI flow. Mocked predictions verify application behavior; they do not evaluate model accuracy. A real printed-field inference was also verified locally. Mouse gestures and theme appearance need a real-browser check; the Streamlit test harness cannot establish those.

Use temporary directories and mocked OCR for deterministic unit tests. Do not load large models during ordinary tests or modify the developer's real `data/` files. Put model-evaluation scripts and results outside the regular test suite and clearly identify datasets and metrics.

## Manual checks before sharing a change

1. Choose an example and draw a field with the mouse; adjust and remove it, then Undo.
2. Add and adjust a field using the keyboard. Leave and reopen the editor to verify its draft.
3. Extract two distinct forms. Check the Excel images and row/field associations.
4. Run recognition, inspect errors, correct a field, and reopen the application.
5. Generate the text workbook and check the correction. Edit again and confirm the old download becomes unavailable until regeneration.
6. Check layout preview and recoverable removal. Exercise empty and failed states.

## Changes and limitations

Keep image extraction independent of OCR. Preserve original inputs, image evidence, crop mappings and manual corrections. Reusing a layout must remain optional. Keep uncertain/failed recognition visible and do not invent confidence scores.

Potential improvements include line segmentation, field validators, clearer model-loading progress, robust workspace portability, document registration and concurrent-write protection. These are future directions, not implemented guarantees.

Submit a branch or pull request describing the problem, resulting behavior, test command and any remaining limitations. Do not commit personal forms, OCR records, generated workbooks, model caches or credentials. Keep third-party example attribution intact.
