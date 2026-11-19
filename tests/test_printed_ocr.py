from pathlib import Path
import pytest
from src.printed_ocr import find_tesseract


def test_explicit_executable_and_invalid_override(tmp_path,monkeypatch):
    executable=tmp_path/'tesseract.exe'
    executable.write_bytes(b'test fixture only')
    monkeypatch.setattr('src.printed_ocr.shutil.which',lambda name:None)
    monkeypatch.setenv('TESSERACT_CMD',str(executable))
    assert find_tesseract()==str(executable)
    monkeypatch.setenv('TESSERACT_CMD',str(tmp_path/'missing.exe'))
    with pytest.raises(RuntimeError,match='TESSERACT_CMD'):
        find_tesseract()


def test_windows_default_discovery_without_path(tmp_path,monkeypatch):
    monkeypatch.delenv('TESSERACT_CMD',raising=False)
    monkeypatch.setattr('src.printed_ocr.shutil.which',lambda name:None)
    monkeypatch.setenv('ProgramFiles',str(tmp_path))
    executable=tmp_path/'Tesseract-OCR'/'tesseract.exe'
    executable.parent.mkdir()
    executable.write_bytes(b'test fixture only')
    assert Path(find_tesseract())==executable
