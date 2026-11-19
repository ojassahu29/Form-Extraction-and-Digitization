from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from .excel_manager import validate_workbook
from .manifest_manager import read, write

def export_fingerprint(image_book, manifest, results):
    digest = hashlib.sha256(Path(image_book).read_bytes())
    digest.update(json.dumps([manifest, results], sort_keys=True).encode())
    return digest.hexdigest()

def export_state(image_book, manifest, results, output):
    metadata = read(Path(str(output) + '.state.json'))
    if not Path(output).exists() or not metadata or not Path(image_book).exists():
        return False, None
    return metadata.get('fingerprint') == export_fingerprint(image_book, manifest, results), metadata.get('generated_at')

def export(image_book, manifest, results, output):
    validate_workbook(image_book, manifest)
    source = load_workbook(image_book, read_only=True)
    headers = [cell.value for cell in source.active[1]]
    source.close()
    wb = Workbook()
    ws = wb.active
    ws.title = "Extracted Text"
    ws.append(headers)
    status = wb.create_sheet("Review_Status")
    status.append(["Source_Form_ID", "Field", "Excel_Cell", "Status", "Review_Status", "Prediction", "Reason", "Error", "Model"])
    lookup = {r["image_id"]: r for r in results}
    by_row = {}
    for item in manifest:
        by_row.setdefault(item["excel_row"], []).append(item)
    for row_number in sorted(by_row):
        items = by_row[row_number]
        ws.cell(row_number, 1, items[0]["source_id"])
        for item in items:
            result = lookup.get(item["image_id"])
            if result:
                value = result["corrected_text"] if result["corrected_text"] is not None else result["prediction"]
                ws[f"{item['excel_column']}{row_number}"] = value
                status.append([item["source_id"], item["field"], f"{item['excel_column']}{row_number}", result["status"], result["review_status"], result["prediction"], result["reason"], result["error"], result["model"]])
            else:
                status.append([item["source_id"], item["field"], f"{item['excel_column']}{row_number}", "NOT_RUN", "PENDING", "", "OCR not run", "", ""])
    for sheet in wb:
        sheet.freeze_panes = "B2"
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        for col in sheet.columns:
            sheet.column_dimensions[col[0].column_letter].width = 25
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)
    write(Path(str(output) + '.state.json'), {'fingerprint': export_fingerprint(image_book, manifest, results), 'generated_at': datetime.now(timezone.utc).isoformat()})
    return output
