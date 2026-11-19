# Form Extraction and Digitization

A local Python application for turning selected fields in scanned forms into structured Excel data. Draw regions on each form, preserve the cropped images, recognize their text, and review or correct the results before exporting.

Developed by **Ojas Sahu**.

## Install and launch

Use Python 3.10–3.12. On Windows PowerShell:

```powershell
git clone https://github.com/ojassahu29/Form-Extraction-and-Digitization.git
cd Form-Extraction-and-Digitization
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local address printed in the terminal, normally http://localhost:8501. Using the explicit `.venv` interpreter avoids missing-package errors from a global Python installation.

For a complete first-form walkthrough, see [USER_GUIDE.md](USER_GUIDE.md). For code structure, testing and development, see [CONTRIBUTING.md](CONTRIBUTING.md).

On Linux/macOS:

```bash
git clone https://github.com/ojassahu29/Form-Extraction-and-Digitization.git
cd Form-Extraction-and-Digitization
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

For printed recognition on Ubuntu/Debian, install `tesseract-ocr` and `tesseract-ocr-eng` through your system package manager. On macOS with Homebrew, use `brew install tesseract`.

For printed text, install the local Tesseract engine:

```powershell
winget install --id UB-Mannheim.TesseractOCR -e
```

The app searches PATH and standard Windows Tesseract folders. For a custom installation, set `TESSERACT_CMD` to its executable path.

Handwriting recognition uses `microsoft/trocr-base-handwritten` through Transformers and PyTorch. Its weights download on first use and are cached locally. CPU is supported, with CUDA used when available. No paid recognition service is required.

## Workflow

1. **Choose forms:** upload PDF, JPEG or PNG files, or select a bundled example. Multiple uploads and local folder import are supported.
2. **Mark & extract:** draw rectangles around answers and assign unique column names. Every form can have different regions. Save fields to extract crops and update the image workbook. Drafts autosave as inputs are committed; Undo and keyboard position/size controls are available.
3. **Check images:** verify the saved crops for the selected form. Select All forms to inspect the wider dataset.
4. **Text workspace:** recognize the selected fields, compare predictions with crop images, save corrections, and generate the latest text workbook. Outdated exports must be regenerated before download.

Saving a reusable layout is optional. Choose **Use a saved layout** only for forms with matching structure. Layout previews, recoverable layout removal and batch extraction are under optional tools. Resolution scaling does not automatically align different designs.

## Two independent phases

**Image extraction** saves the original input, source-specific regions, PNG crops, a manifest and `Image_extract.xlsx` with real embedded images. It runs without recognition.

**Text recognition** validates the persisted workbook and manifest and loads their mapped crops. It can run after restarting the application:

```powershell
.\.venv\Scripts\python.exe -m src.run_ocr
```

Original predictions remain separate from human corrections. Failed and unresolved fields remain traceable in the exported `Review_Status` sheet.

## Files and directories

| Location | Purpose |
|---|---|
| `app.py` | Streamlit interface |
| `src/` | Loading, drawing, extraction, persistence, OCR, review and export |
| `tests/` | Automated regression and interface tests |
| `templates/` | Optional reusable layout JSON; removed layouts go into `trash/` |
| `data/input/` | Saved source documents |
| `data/crops/` | Original-resolution field crops |
| `data/manifests/` | Crop mappings, drafts, source-specific regions and recognition results |
| `data/output/Image_extract.xlsx` | Embedded crop images |
| `data/output/Text_extraction.xlsx` | Recognized and corrected text |
| `demo/internet_examples/` | Public example scans, reference annotations and source attribution |
| `backups/` | Existing recovery copies; not application input |

Keep each image workbook with its corresponding manifest and crop files. Do not manually edit the workbook's source IDs or field mappings.

Git excludes working forms, crops, recognition results, Excel outputs, personal saved layouts, local backups and the virtual environment. These folders are initialized on launch; cloning the repository starts a fresh workspace. Public example scans and their attribution are included.

## Examples

The example picker includes public FUNSD scans containing handwritten entries. Attribution and suggested fields are in `demo/internet_examples/REAL_SAMPLES.md`. Reference annotations are dataset labels, not predictions from this application. Signatures and poor-quality scans may require manual transcription.

Optional synthetic examples can be generated and processed separately:

```powershell
.\.venv\Scripts\python.exe demo/make_sample.py
.\.venv\Scripts\python.exe -m demo.prepare_demo
```

Synthetic handwriting-style fonts are not evidence of performance on genuine handwriting. `demo/download_examples.py` optionally downloads a separate attributed synthetic sample set; see that script's dataset source.

## Tests

```powershell
python run_tests.py
```

The runner selects `.venv` when present and uses a fresh temporary path to avoid older Windows directory-permission problems. Tests include mocked recognition for deterministic pipeline checks; these are separate from real model inference.

## Limitations and troubleshooting

- TrOCR is intended for cropped handwritten lines. Signatures, long paragraphs, complex multiline fields and unsupported languages are unreliable. Inspect and correct predictions.
- Unknown mode routes to TrOCR and flags review; it does not classify handwriting versus printed text.
- Review flags and multiline detection are heuristics, not calibrated confidence scores.
- Initial model loading may take time before field progress advances. Check connectivity for first-time downloads.
- Printed-text failures: check engine readiness on the recognition screen. After fixing the installation, retry a failed field from Review.
- Workbook access error: close the workbook in Excel before regenerating it. Restore matching manifests and crops if mappings were changed externally.
- Draft text saves when Enter is pressed or focus leaves the input. Uncommitted keystrokes may be lost on a browser close.
- Theme settings are in `.streamlit/config.toml`; the palette is documented in `DESIGN.md`.
