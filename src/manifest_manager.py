import json
import os
import tempfile
from pathlib import Path
from .config import MANIFEST, RESULTS, ensure_dirs

def read(path=MANIFEST):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as file:
        json.dump(data, file, indent=2)
        temp = file.name
    os.replace(temp, path)

def results():
    return read(RESULTS)

def save_results(rows):
    write(RESULTS, rows)
