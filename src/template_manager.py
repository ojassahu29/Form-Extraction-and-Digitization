import json
import re
import uuid
from pathlib import Path
from .config import TEMPLATES, ensure_dirs
from .region_selector import pixel_box

def template_path(name):
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")
    if not safe:
        raise ValueError("Template name is required")
    return TEMPLATES / f"{safe}.json"

def validate(template):
    fields = template.get("fields", [])
    names = [f.get("name", "").strip() for f in fields]
    if not fields or not all(names) or len(names) != len(set(names)) or "Source_Form_ID" in names:
        raise ValueError("Field names must be nonempty, unique, and cannot be Source_Form_ID")
    for field in fields:
        if field.get("mode") not in ("handwritten", "printed", "auto"):
            raise ValueError("Invalid recognition mode")
        if int(field.get("page", 0)) < 1:
            raise ValueError("Page numbers start at 1")
        pixel_box(field["box"], 10000, 10000)

def save(template):
    ensure_dirs()
    validate(template)
    name = template.get("name", "")
    path = template_path(name)
    path.write_text(json.dumps(template, indent=2), encoding="utf-8")
    return path

def load(name):
    return json.loads(template_path(name).read_text(encoding="utf-8"))

def list_templates():
    ensure_dirs()
    return [p.stem for p in sorted(TEMPLATES.glob("*.json"))]

def delete(name):
    path = template_path(name)
    archived = TEMPLATES / 'trash' / f'{path.stem}_{uuid.uuid4().hex}.json'
    archived.parent.mkdir(parents=True, exist_ok=True)
    path.rename(archived)
    return archived

def restore(archived):
    archived = Path(archived).resolve()
    if archived.parent != (TEMPLATES / 'trash').resolve():
        raise ValueError('Only removed layouts can be restored')
    template = json.loads(archived.read_text(encoding='utf-8'))
    path = template_path(template['name'])
    if path.exists():
        raise ValueError('A layout with that name already exists; rename it before restoring')
    archived.rename(path)
    return path
