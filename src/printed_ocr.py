"""Locate a local Tesseract installation, including Windows installs off PATH."""
import os
import shutil
from pathlib import Path


def find_tesseract():
    configured = os.environ.get('TESSERACT_CMD')
    if configured:
        located = shutil.which(configured)
        if located:
            return located
        if Path(configured).is_file():
            return str(Path(configured))
        raise RuntimeError('TESSERACT_CMD points to a missing executable. Correct that setting or unset it to use automatic discovery.')
    located = shutil.which('tesseract')
    if located:
        return located
    candidates = [Path(os.environ.get(env, fallback)) / relative for env,fallback,relative in (
        ('ProgramFiles', 'C:/Program Files', 'Tesseract-OCR/tesseract.exe'),
        ('ProgramFiles(x86)', 'C:/Program Files (x86)', 'Tesseract-OCR/tesseract.exe'),
        ('LOCALAPPDATA', str(Path.home()/'AppData/Local'), 'Programs/Tesseract-OCR/tesseract.exe'),
        ('LOCALAPPDATA', str(Path.home()/'AppData/Local'), 'Tesseract-OCR/tesseract.exe'),
    )]
    return next((str(p) for p in candidates if p.is_file()), None)


def configure_tesseract():
    import pytesseract
    executable = find_tesseract()
    if not executable:
        raise RuntimeError('Printed-text recognition needs the Tesseract desktop engine. Install it with: winget install --id UB-Mannheim.TesseractOCR -e . Handwritten fields use TrOCR instead. Existing crops and corrections are safe.')
    pytesseract.pytesseract.tesseract_cmd = executable
    return pytesseract


def printed_backend_status():
    try:
        backend = configure_tesseract()
        version = str(backend.get_tesseract_version()).splitlines()[0]
        languages = backend.get_languages(config='')
        if 'eng' not in languages:
            return False, 'Tesseract was found, but its English language data is missing. Install the English language data and retry.'
        return True, f'Printed-text engine ready: Tesseract {version} (English).'
    except Exception as exc:
        return False, str(exc)
