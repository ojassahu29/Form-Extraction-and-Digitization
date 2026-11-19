# Example forms

The bundled real scans and source attribution are described in [REAL_SAMPLES.md](REAL_SAMPLES.md). Choose them in the app; no reusable layout is required.

Optionally download a separate synthetic sample set from the project root:

```powershell
.\.venv\Scripts\python.exe -m demo.download_examples
```

The script downloads five forms from [Hyperbots Inc., Synthetic Handwritten Forms](https://huggingface.co/datasets/hyperbots-inc/synthetic-handwritten-forms), licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It also saves derived three-field templates, source records and expected values. Keep attribution when redistributing those samples. Their handwriting is font-rendered and personal details are fictional; they do not replace testing on genuine handwriting.
