# Real scanned forms for manual handwriting tests

Source: [FUNSD](https://guillaumejaume.github.io/FUNSD/), Jaume, Ekenel and Thiran, *FUNSD: A Dataset for Form Understanding in Noisy Scanned Documents* (2019). Downloaded from the official `dataset.zip`, testing split. Images are unchanged public historical scans, not fictional identities or synthetic handwriting. Follow the source site's dataset terms for reuse. See `genuine_sources.json` for each original archive path.

| Local file | Actual document | Suggested handwritten field |
|---|---|---|
| genuine_application.png | Records retention schedule reconciliation | Names on the re-labelled-by and filed-by lines |
| genuine_purchase_order.png | Supplier proposal | Handwritten amount near lower right; a difficult example |
| genuine_lab_request.png | Facsimile cover sheet | Page count and file number in the top table |
| genuine_fax_note.png | Fax cover note | Extension number and operator name |
| genuine_report.png | Test article receipt | Handwritten date near bottom left |

Open Choose forms in the app, select a **Real scan** example, and click **Use this example and draw fields**. Draw around a handwritten entry, name its column, then Save fields and extract this form. Continue to image results, recognition and review. No preset template is required or supplied.

The accompanying `_annotations.json` files are the dataset's original transcriptions and bounding boxes for reference. They are not predictions from this application. Image quality varies, and signatures or illegible entries may require manual transcription. No real OCR results have been generated for these samples yet.
