from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

def image_workbook(path, manifest):
    path = Path(path)
    # Rebuild from the durable manifest so old drawings never duplicate on append.
    existing = Workbook()
    ws = existing.active
    ws.title = "Extracted Images"
    headers = [c.value for c in ws[1]] if ws.max_row > 1 or ws.cell(1, 1).value else []
    if not headers:
        headers = ["Source_Form_ID"]
    for item in manifest:
        if item["field"] not in headers:
            headers.append(item["field"])
    for col, header in enumerate(headers, 1):
        cell = ws.cell(1, col, header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="243B53")
        ws.column_dimensions[get_column_letter(col)].width = 27
    grouped = {}
    for item in manifest:
        grouped.setdefault(item["source_id"], []).append(item)
    for source_id, items in grouped.items():
        row = items[0]["excel_row"]
        ws.cell(row, 1, source_id)
        ws.row_dimensions[row].height = 75
        for item in items:
            col = headers.index(item["field"]) + 1
            item["excel_column"] = get_column_letter(col)
            img = ExcelImage(item["crop_path"])
            ratio = min(180 / img.width, 90 / img.height, 1)
            img.width *= ratio
            img.height *= ratio
            ws.add_image(img, f"{item['excel_column']}{row}")
    ws.freeze_panes = "B2"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing.save(path)

def validate_workbook(path, manifest):
    if not Path(path).exists():
        raise FileNotFoundError(path)
    wb = load_workbook(path)
    ws = wb.active
    headers = {c.column_letter: c.value for c in ws[1]}
    anchors = {f"{get_column_letter(img.anchor._from.col + 1)}{img.anchor._from.row + 1}" for img in ws._images}
    for item in manifest:
        cell = f"{item['excel_column']}{item['excel_row']}"
        if ws.cell(item["excel_row"], 1).value != item["source_id"] or headers.get(item["excel_column"]) != item["field"] or cell not in anchors or not Path(item["crop_path"]).is_file():
            raise ValueError(f"Workbook/manifest mismatch at {cell}")
    return True
