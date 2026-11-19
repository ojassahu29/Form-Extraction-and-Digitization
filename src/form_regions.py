"""Persist regions for one source form without creating a reusable template."""
import hashlib
from pathlib import Path
from .config import MANIFESTS
from .manifest_manager import read, write
from .template_manager import validate

def key(path):
    return hashlib.sha256(str(Path(path).resolve()).encode()).hexdigest()[:20]

def load_regions(path, directory=MANIFESTS):
    saved = Path(directory) / f"form_regions_{key(path)}.json"
    return read(saved) if saved.exists() else None

def save_regions(path, fields, width, height, directory=MANIFESTS):
    config = {"name": f"form_{key(path)}", "source_path": str(Path(path).resolve()),
              "reference_width": width, "reference_height": height, "fields": fields}
    validate(config)
    write(Path(directory) / f"form_regions_{key(path)}.json", config)
    return config
