# Handwritten Form Digitization

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Desktop users who need to digitize handwritten or printed fields from scanned forms. First-time users must be able to complete the workflow without editing code or learning template terminology.

## Product Purpose

Preserve selected field images as evidence, convert them into structured text, and support human correction. Success produces image and text Excel workbooks with reliable source-to-field associations.

## Operating Context

Local Streamlit application, primarily on Windows. Users import PDF/JPEG/PNG forms or choose an example, mark regions, inspect crops, independently run recognition, review and correct text, then export. Forms may have distinct layouts; reusable layouts are optional.

## Capabilities and Constraints

- Image extraction runs without OCR and persists sources, regions, crops, embedded Excel images and a manifest.
- Recognition reads persisted extraction outputs after restart. Handwriting uses TrOCR; printed fields use local Tesseract. Unknown mode routes to handwriting recognition and requests review.
- Preserve original predictions separately from human corrections. Changed regions must not inherit corrections from different crops.
- Draw boxes for this form is the default. Use a saved layout reveals the optional selector and a black-on-white preview.
- Keep processing local, support CPU and optional CUDA, and require no paid OCR service. Pretrained model downloads may require an initial internet connection.
- Do not promise automatic layout registration, reliable signature transcription, broad multilingual support or calibrated confidence.
- Preserve user data during interface changes. Examples are not automatically inserted into working records.

## Terminology and Voice

Direct task language: choose forms, mark and extract, check images, recognize text, review and correct, download. Explain layout reuse and batch processing separately from the individual-form path. Surface uncertainty and recovery steps clearly.

## Evidence on Hand

Source code, automated tests, public example scans and dataset reference annotations are in the repository. Tests using mocked OCR verify software behavior, not model quality. Do not fabricate benchmark scores, recognition results or claims about how the software was authored.

## Product Principles

1. Make one-form extraction understandable without training.
2. Preserve image evidence and traceability.
3. Make recognition reviewable and corrections durable.
4. Keep layouts optional and support distinct forms.
5. Keep work local and recoverable across restarts.

## Attribution

Application credit: Ojas Sahu. Public sample datasets retain their own source attribution and terms.
