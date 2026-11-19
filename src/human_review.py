from .manifest_manager import read, write

def correct(path, image_id, text, confirm=True):
    rows = read(path)
    for row in rows:
        if row["image_id"] == image_id:
            row["corrected_text"] = text
            row["status"] = "MANUALLY_CORRECTED"
            row["review_status"] = "CONFIRMED" if confirm else "PENDING"
            write(path, rows)
            return row
    raise KeyError(image_id)

def flag(path, image_id, reason="Flagged by user"):
    rows = read(path)
    for row in rows:
        if row["image_id"] == image_id:
            row["status"] = "NEEDS_REVIEW"
            row["review_status"] = "PENDING"
            row["reason"] = reason
            write(path, rows)
            return
    raise KeyError(image_id)
