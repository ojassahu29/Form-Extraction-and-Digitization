# User guide

## Start the application

Follow the [README installation steps](README.md#install-and-launch), then open the local address shown in your terminal. Leave that terminal running while using the app. All processing and files stay on your computer, except the initial model download.

## First example: from a form to text

1. Open **Choose forms**. Select **Real scan: records reconciliation (handwritten names)** in the example picker and click **Use this example and draw fields**. To use your own document instead, upload a PDF, JPEG or PNG and save it.
2. In **Mark & extract**, leave **Draw boxes for this form** selected. For a PDF, select the page containing the answers you want.
3. On the form, press and hold the left mouse button at one corner of a handwritten answer. Drag to the opposite corner and release. Draw around the written value, rather than the printed label. Start with one name or date on a single line.
4. Find **Box 1** beside the form. Enter a column name such as `Filed By`. Choose **Handwritten** for handwriting or **Printed / typed** for typed text. Check the crop preview to confirm the entire answer is visible.
5. Add more boxes if needed. Move by dragging inside a box, resize with its lower-right handle, and remove with its × control or **Remove box**. **Undo last edit** restores a prior edit.
6. For keyboard operation, Tab to **Add box using keyboard** and press Enter. Open its **Position and size** controls, adjust values, and apply them. You can complete naming and extraction with standard keyboard navigation.
7. Leave **Also save these boxes as a reusable layout** unchecked for individual forms. Click **Save fields and extract this form**. This creates image crops and updates the image workbook; you do not need a template.
8. In **Check images**, inspect the cropped answers. Download the image workbook to open it in Excel. Each source form is one row; each named field is a column with its actual image embedded. Return to the editor if a crop is incomplete.
9. Click **Recognize these images** to enter the **Text workspace**. Verify the selected form. **All forms** explicitly expands the scope. Click **Run Text Extraction** once and wait; first-use TrOCR downloads and initialization can take several minutes before the first field finishes.
10. Open **Review & correct**. Compare each crop with its prediction. Enter the correct transcription and click **Save correction and next unconfirmed**. Inspect successful-looking predictions too: nonempty text does not guarantee correctness. If recognition fails, you can retry or transcribe manually.
11. Open **Download text**. The export includes all saved forms, not only the form selected for review. Inspect the unresolved count, click **Generate latest Text_extraction.xlsx**, then download it. After later corrections, regenerate before downloading again.
12. Open the text workbook in Excel. Compare its source IDs, named columns and values with the image workbook. Inspect **Review_Status** for pending fields, errors and original predictions.

## Save and resume

Drafts save locally when controls commit their values; press Enter or leave a text input to commit it. A browser close can lose uncommitted keystrokes. Saving fields preserves source-specific regions and extracts crops. Reopening the app restores persisted forms, regions and corrections. Keep the `data/` directory when transferring an existing working dataset to another machine; the stored paths currently refer to the originating machine, so use the same workspace path or re-extract there.

## Different forms and reusable layouts

For a different form, select it and draw its own boxes. Similar column names can share workbook columns even when field positions differ. Use a different name when the meaning differs.

For repeated layouts, check **Also save these boxes as a reusable layout** and give it a name before extraction. On a matching form, choose **Use a saved layout**, select it, inspect the PNG preview and confirm that the boxes match. Adjusting one form's boxes does not automatically update the reusable layout. Resolutions can vary; different designs are not automatically aligned.

**Optional tools & help → Batch extraction** applies a saved layout to several selected forms. All selected forms must match that layout. Previously processed forms are skipped unless replacement is enabled. **Saved layouts** includes preview, removal and restore controls. Removed reusable layouts do not delete existing crops.

## Files you receive

- `data/output/Image_extract.xlsx`: embedded image evidence, generated before OCR.
- `data/output/Text_extraction.xlsx`: predictions and saved corrections, with a Review_Status sheet.
- `data/crops/`: original-resolution PNG crop files.
- `data/manifests/`: mappings, source-specific regions, drafts and recognition records needed to resume.

Do not rename or edit mapping IDs in the image workbook. Close Excel before overwriting either workbook.

## Run recognition without the UI

After extracting images, close or leave the UI and run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m src.run_ocr
```

On Linux/macOS, use `.venv/bin/python -m src.run_ocr`. This validates the saved image workbook and manifest, recognizes all mapped crops, preserves manual corrections and writes the text workbook. You can reopen the UI afterward to review results. Avoid running simultaneous extraction/OCR jobs against the same workspace.

## Common problems

| Problem | Action |
|---|---|
| Missing Python module | Install `requirements.txt` using the same `.venv` interpreter used to launch the app. |
| Tesseract unavailable | Install the desktop engine using the README instructions; check readiness in Text workspace, then retry the failed field. Installing pytesseract alone is insufficient. |
| Initial OCR appears slow | Allow time for pretrained-weight download and CPU initialization; check network access and error details if loading fails. |
| Wrong recognition | Check crop boundaries and writing mode. For difficult handwriting, use manual correction. |
| Cannot save Excel | Close the workbook in Excel and retry. |
| Workbook/manifest mismatch | Restore the matching workbook, manifest and crops, or re-extract the source forms. |
| Download is outdated | Generate the latest text workbook after recognition, correction or extraction changes. |

The included historical scans have noisy handwriting; signatures and long multiline answers can be especially difficult. The app does not guarantee transcription accuracy. Dataset annotations are reference material, not application-generated predictions; source attribution is in the examples folder.
