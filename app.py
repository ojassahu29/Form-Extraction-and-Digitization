import hashlib
from pathlib import Path
import streamlit as st
import re
from src.image_extractor import import_form
from src.region_selector import crop
from src.canvas import select_regions
from src.config import INPUT, IMAGE_BOOK, TEXT_BOOK, MANIFEST, RESULTS, ensure_dirs
from src.document_loader import pages, preview, SUPPORTED
from src.region_selector import normalize_box
from src.template_manager import save, load, list_templates, delete
from src.image_extractor import process
from src.form_regions import load_regions, save_regions
from src.template_preview import layout_png
from src.manifest_manager import read
from src.ocr_engine import run
from src.human_review import correct, flag
from src.export_manager import export, export_state
from src.editor_ui import edit_fields
from src.editor_state import mark_extracted
from src.template_manager import restore
from src.printed_ocr import printed_backend_status

ensure_dirs()
st.set_page_config(page_title="Handwritten Form Digitization", layout="wide")
st.html("""<style>
[data-testid="stMainBlockContainer"] {max-width: 1500px; padding-top: 2rem;}
h1,h2,h3 {letter-spacing: -0.02em;}
[data-testid="stSidebar"] {border-right: 1px solid #1E293B;}
button[kind="primary"] {color: #020617; font-weight: 600;}
button[kind="primary"]:disabled {color: inherit;}
input,textarea {caret-color: #AFF33E;}
::selection {background: #AFF33E; color: #020617;}
:focus-visible {outline-offset: 3px;}
@media(max-width: 760px) {
  [data-testid="stMainBlockContainer"] {padding: 1.25rem 1rem;}
}
</style>""")
st.title("Form digitization workspace")
st.caption("BITS Pilani Goa Campus · Handwritten and printed form extraction")
st.caption("Developed by Ojas Sahu")
NAV = ["Help", "Choose forms", "Mark & extract", "Saved layouts", "Batch extraction", "Check images", "Recognize text", "Review & correct", "Download text"]
MAIN = ["Choose forms", "Mark & extract", "Check images", "Text workspace"]

def go(destination):
    st.session_state["next_page"] = destination
    st.rerun()

def route_changed():
    st.session_state["route"] = NAV[6] if st.session_state["main_route"] == MAIN[3] else st.session_state["main_route"]

if "next_page" in st.session_state:
    st.session_state["route"] = st.session_state.pop("next_page")
    if st.session_state["route"] in NAV[6:]:
        st.session_state["text_step"] = st.session_state["route"]
section = st.session_state.get("route", NAV[1])
if section not in NAV:
    section = NAV[1]
main_section = MAIN[3] if section in NAV[6:] else section
if main_section in MAIN:
    st.session_state["main_route"] = main_section
st.sidebar.radio("Your workspace", MAIN, key="main_route", on_change=route_changed)
section = st.session_state.get("route", section)
if section in NAV[6:]:
    section = st.radio("Text workflow", NAV[6:], index=NAV[6:].index(section), horizontal=True, key="text_step")
    st.session_state["route"] = section
st.sidebar.caption("Phase 1: choose, mark and check images. Phase 2: recognize, review and download text. Layout saving is optional.")
with st.sidebar.expander("Optional tools & help"):
    for destination in [NAV[3], NAV[4], NAV[0]]:
        if st.button(destination, key='nav_'+destination):
            go(destination)
if "notice" in st.session_state:
    st.success(st.session_state.pop("notice"))

def readable(source):
    return re.sub(r"^(?:[0-9a-f]{16}_)+", "", Path(source).name)

def source_scope(records, key):
    sources = list(dict.fromkeys(r['source_id'] for r in records))
    if not sources:
        return []
    options = sources + ['All forms']
    preferred = st.session_state.get('scope_selection')
    if preferred not in options:
        preferred = next((v for v in sources if v.endswith(Path(st.session_state.get('active_form','__none__')).name)), sources[0])
    widget_key = 'scope_current'
    if st.session_state.get(widget_key) not in options:
        st.session_state.pop(widget_key, None)
    selected = st.selectbox('Form to work on', options, index=options.index(preferred), format_func=lambda x: readable(x) if x!='All forms' else x, key=widget_key)
    st.session_state['scope_selection'] = selected
    if selected != 'All forms':
        for row in records:
            if row['source_id']==selected:
                st.session_state['active_form'] = row.get('source_path',st.session_state.get('active_form',''))
                break
    return records if selected=='All forms' else [r for r in records if r['source_id']==selected]

def current_results(records):
    ids = {r['image_id'] for r in records}
    return [r for r in read(RESULTS) if r['image_id'] in ids]

def recovery(message, exc):
    st.error(message)
    with st.expander('Error details for troubleshooting'):
        st.code(str(exc))

def next_step(label, destination, key=None):
    if st.button(label, key=key, type="primary"):
        go(destination)


def available_forms():
    return sorted(p for p in INPUT.iterdir() if p.suffix.lower() in SUPPORTED)

def show_layout(template, key):
    page_numbers = sorted({int(f["page"]) for f in template["fields"]})
    for number in page_numbers:
        png = layout_png(template, number)
        st.image(png, caption=f"{template['name']} · page {number} · saved field positions", width=300)
        st.download_button(f"Download page {number} layout PNG", png, file_name=f"layout_page_{number}.png", mime="image/png", key=f"layout_download_{key}_{number}")
    st.caption("Black outlines show saved boxes, not recognized text. Check that they match the form before extracting.")

def chosen_template(key="template"):
    names = list_templates()
    if not names:
        st.info("No reusable templates saved. For an individual form, use Draw & name fields and save its crops directly.")
        return None
    template = load(st.selectbox("Template", names, index=names.index(st.session_state["saved_template"]) if st.session_state.get("saved_template") in names else 0, key=key))
    with st.expander("Preview this saved layout", expanded=key == "manage_template"):
        show_layout(template, key)
    return template

if section == "Help":
    st.header("Turn a form into a spreadsheet")
    st.write("First save pictures of the answers you need. Then recognize those pictures as text and correct any mistakes.")
    st.subheader("Try one form from start to finish")
    st.markdown("1. **Choose a form** — upload your own or select an example.\n2. **Mark & extract** — draw boxes, name each field, then save its image crops. No template is required.\n3. **Check images** — confirm each crop contains the full answer.\n4. **Text workspace** — recognize, review corrections, then download the latest text workbook.")
    next_step("Get started: choose a form", NAV[1])
    st.divider()
    st.write(f"Your workspace has **{len(available_forms())} forms**, **{len(read(MANIFEST))} saved crops**, and **{len(read(RESULTS))} recognition results**.")

elif section == "Choose forms":
    st.header("Choose a form")
    st.write("Choose a ready-made example or upload your own. Saving a form makes it available in the next step.")
    example_dir = Path(__file__).parent / "demo"
    examples = sorted((example_dir / "internet_examples").glob("genuine_*.png")) + sorted((example_dir / "internet_examples").glob("*.jpg")) + sorted(example_dir.glob("sample_form*.png"))
    if examples:
        labels = {"hw-0001.jpg": "KYC form", "hw-0002.jpg": "Bank details", "hw-0003.jpg": "Credit application", "hw-0004.jpg": "Patient intake", "hw-0005.jpg": "Insurance claim"}
        labels.update({"genuine_application.png": "Real scan: records reconciliation (handwritten names)", "genuine_purchase_order.png": "Real scan: supplier proposal (handwritten amounts)", "genuine_lab_request.png": "Real scan: fax sheet (handwritten page count and file number)", "genuine_fax_note.png": "Real scan: fax note (handwritten extension and operator)", "genuine_report.png": "Real scan: receipt (handwritten date)"})
        example = st.selectbox("Try an example", examples, format_func=lambda p: labels.get(p.name, p.stem.replace("_", " ")))
        if example.name.startswith("genuine_"):
            st.caption("Public historical scan from FUNSD, with genuine handwritten entries. Start with a short name, number or date; signatures are difficult to transcribe.")
        else:
            st.caption("Synthetic example containing fictional data and font-rendered handwriting.")
        if st.button("Use this example and draw fields", type="primary"):
            target, _ = import_form(example)
            st.session_state["active_form"] = str(target)
            go(NAV[2])
    st.divider()
    uploads = st.file_uploader("Upload PDF, JPEG or PNG forms", type=["pdf", "jpg", "jpeg", "png"], accept_multiple_files=True)
    if uploads and st.button("Save uploaded forms"):
        for upload in uploads:
            content = upload.getvalue()
            digest = hashlib.sha256(content).hexdigest()[:16]
            target = INPUT / f"{digest}_{Path(upload.name).name}"
            target.write_bytes(content)
            st.success(f"Saved {target.name}")
    if available_forms():
        next_step("Continue to draw fields", NAV[2])
    st.subheader("Import from a local folder (optional)")
    folder = st.text_input("Or import all supported forms from a local folder path")
    if st.button("Import folder") and folder:
        root = Path(folder).expanduser()
        if not root.is_dir():
            st.error("Folder does not exist on this computer")
        else:
            for source in sorted(root.iterdir()):
                if source.is_file() and source.suffix.lower() in SUPPORTED:
                    content = source.read_bytes()
                    target = INPUT / f"{hashlib.sha256(content).hexdigest()[:16]}_{source.name}"
                    target.write_bytes(content)
                    st.write(f"Imported {source.name}")

elif section == "Mark & extract":
    st.header("Mark fields and extract this form")
    st.write("Draw fields for this individual form and save its crops for OCR. Each form can have different boxes. Saving a reusable template is optional.")
    forms = available_forms()
    if not forms:
        st.info("Choose or upload a form before marking fields.")
        next_step("Choose a form", NAV[1])
    else:
        active = st.session_state.get("active_form")
        form = st.selectbox("Form to mark", forms, index=next((i for i,p in enumerate(forms) if str(p)==active),0), format_func=lambda p: re.sub(r"^(?:[0-9a-f]{16}_)+", "", p.name))
        st.session_state["active_form"] = str(form)
        all_pages = list(pages(form))
        page_num = st.selectbox("Reference page", [n for n, _ in all_pages])
        original = dict(all_pages)[page_num]
        shown = preview(original)
        saved_regions = load_regions(form)
        region_mode = st.radio("How do you want to mark this form?", ["Draw boxes for this form", "Use a saved layout"], horizontal=True, key=f"region_mode_{form.name}")
        existing_name = "own_boxes"
        existing = saved_regions
        if region_mode == "Use a saved layout":
            layouts = list_templates()
            if not layouts:
                st.info("No layouts saved yet. Select Draw boxes for this form. You can save a reusable layout after naming its fields.")
                st.stop()
            existing_name = st.selectbox("Choose a saved layout", layouts, key=f"region_source_{form.name}")
            existing = load(existing_name)
            with st.expander("Preview this layout before using it", expanded=True):
                show_layout(existing, f"editor_{form.name}")
            st.caption("The selected layout's boxes appear on the form below. You can adjust them for this form before extracting.")
        else:
            st.caption("Draw separate boxes for this form. The saved-layout selector is off.")
        if saved_regions and region_mode == "Draw boxes for this form":
            st.caption("Loaded the boxes previously saved for this form. You can adjust them and save again.")
        fields, ready, draft = edit_fields(form, page_num, existing_name, original, shown, existing)
        st.divider()
        st.subheader("Save the crops for OCR")
        st.caption("Your draft is already saved. This action extracts the image crops into Image_extract.xlsx. Saving again replaces this form's earlier extraction.")
        keep_template = st.checkbox("Also save these boxes as a reusable layout", key=f"keep_template_{form.name}")
        template_name = st.text_input("Reusable layout name", key=f"optional_template_{form.name}") if keep_template else ""
        if st.button("Save fields and extract this form", type="primary", disabled=not ready or (keep_template and not template_name.strip())):
            try:
                other_pages = [f for f in saved_regions["fields"] if f["page"] != page_num] if saved_regions else []
                config = save_regions(form, other_pages + fields, original.width, original.height)
                if keep_template:
                    reusable = dict(config, name=template_name.strip())
                    reusable.pop("source_path", None)
                    path = save(reusable)
                    st.session_state["saved_template"] = path.stem
                with st.spinner("Saving crops and updating Excel..."):
                    outcome = process([form], config, force=True)[0][1]
                if outcome != "PROCESSED":
                    st.error(f"Your draft is safe, but extraction did not finish. Close Image_extract.xlsx if open and try again. Details: {outcome}")
                else:
                    mark_extracted(draft)
                    st.session_state.pop('scope_selection',None)
                    for k in list(st.session_state):
                        if k.startswith('scope_'):
                            del st.session_state[k]
                    st.session_state["notice"] = f"Saved {len(config['fields'])} crops for {readable(form)}. Check the images below."
                    go(NAV[5])
            except Exception as exc:
                recovery("Could not extract these fields. Your draft is retained. Check field names, page boundaries and workbook access, then retry.", exc)


elif section == "Saved layouts":
    st.header("Saved field templates")
    st.write("A template remembers your field names and positions. To move boxes or rename fields, open Draw & name fields and select the template there.")
    removed = st.session_state.get('removed_layout')
    if removed:
        if st.button('Undo last layout removal'):
            try:
                restore(removed)
                st.session_state.pop('removed_layout',None)
                st.rerun()
            except Exception as exc:
                recovery('Could not restore the layout. A layout with that name may already exist.',exc)
    template = chosen_template("manage_template")
    if template:
        st.table([{"Column name": f["name"], "PDF page": f["page"], "Writing": f["mode"]} for f in template["fields"]])
        with st.expander("Technical template details"):
            st.json(template)
        next_step("Open the region editor", NAV[2])
        with st.expander("Remove this saved layout"):
            st.caption("This removes only the reusable layout from the picker. Form crops remain intact. You can restore it afterward.")
            confirm = st.checkbox("Remove this layout from the saved list",key='confirm_remove_'+template['name'])
            if st.button("Remove layout",disabled=not confirm):
                st.session_state['removed_layout'] = str(delete(template['name']))
                st.rerun()
    from src.config import TEMPLATES
    trash = sorted((TEMPLATES/'trash').glob('*.json')) if (TEMPLATES/'trash').exists() else []
    if trash:
        with st.expander('Restore a removed layout'):
            archived = st.selectbox('Removed layout',trash,format_func=lambda p: p.stem.rsplit('_',1)[0])
            if st.button('Restore selected layout'):
                try:
                    restore(archived)
                    st.rerun()
                except Exception as exc:
                    recovery('Restore failed. Rename the currently saved layout with the same name before retrying.',exc)

elif section == "Batch extraction":
    st.header("Batch extraction with a saved layout")
    st.write("Optional batch shortcut: apply a reusable template to forms with identical layouts. For distinct forms, use Draw & name fields and save each form directly.")
    template = chosen_template("process_template")
    forms = available_forms()
    selected = st.multiselect("Forms to process", forms, default=[p for p in forms if str(p)==st.session_state.get("active_form")], format_func=lambda p: re.sub(r"^(?:[0-9a-f]{16}_)+", "", p.name))
    st.warning("Batch forms must share the selected template layout. Normalized boxes adapt to resolution; automatic alignment is not provided.")
    force = st.checkbox("Replace previously extracted fields for selected forms", help="Leave unchecked for normal use. Existing forms are skipped to prevent duplicate rows.")
    if st.button("Extract images", disabled=not (template and selected)):
        bar = st.progress(0)
        for i, form in enumerate(selected, 1):
            for source, outcome in process([form], template, force=force):
                st.write(source, outcome)
            bar.progress(i / len(selected))
        st.info("Processing finished. Check the per-form messages above; skipped forms already have saved crops.")
    next_step("Check cropped images and download Excel", NAV[5])

elif section == "Check images":
    st.header("Check the cropped answers")
    records = source_scope(read(MANIFEST), 'images')
    if not records:
        st.info("No crops saved yet. Mark fields on a form and extract them first.")
        next_step("Mark fields", NAV[2])
    else:
        st.write(f"**{len(records)} crops** in the selected scope. Check that each answer is complete before recognition.")
        for item in records:
            with st.expander(f"{readable(item['source_id'])} — {item['field']}", expanded=len(records)<=3):
                st.image(item['crop_path'])
        if IMAGE_BOOK.exists():
            st.download_button("Download image workbook (all forms)", IMAGE_BOOK.read_bytes(), file_name="Image_extract.xlsx")
        next_step("Recognize these images", NAV[6])
        if st.button("Adjust boxes or mark another form"):
            go(NAV[2])

elif section == "Recognize text":
    st.header("Recognize the saved images")
    records = source_scope(read(MANIFEST),'ocr')
    if not records:
        st.info("Save crops from a form before running text recognition.")
        next_step("Mark and extract fields",NAV[2])
    else:
        st.write(f"Recognition will process **{len(records)} fields** from the selected scope. Saved human corrections are preserved.")
        if any(r['mode']=='printed' for r in records):
            printed_ready, printed_message = printed_backend_status()
            if printed_ready:
                st.success(printed_message)
            else:
                st.warning(printed_message)
                st.caption('Printed fields will be recorded as failed until the engine is installed. You can still run handwriting recognition and retain all crops.')
        st.caption("Handwriting uses TrOCR. The first run downloads model weights; setup can take several minutes before the first field finishes. Printed fields require local Tesseract. Predictions need inspection.")
        if st.button("Run Text Extraction",type='primary'):
            bar = st.progress(0)
            try:
                with st.status("Loading recognition model and processing fields...",expanded=True) as status:
                    st.write("Preparing the model. Initial download/loading may take time.")
                    results = run(records, IMAGE_BOOK, RESULTS, progress=lambda n,total:bar.progress(n/total))
                    failed = sum(r['status']=='FAILED' for r in results)
                    status.update(label=f"Recognition finished: {len(results)} fields, {failed} failed. Review the results next.",state='complete')
            except Exception as exc:
                recovery("Recognition could not finish. Your crops are safe. Check the model download/network or printed-text backend, then retry.",exc)
        next_step("Review predictions",NAV[7])

elif section == "Review & correct":
    st.header("Review and correct the text")
    records = source_scope(read(MANIFEST),'review')
    results = current_results(records)
    unrun = len(records)-len(results)
    pending = [r for r in results if r.get('review_status')!='CONFIRMED']
    st.write(f"**{len(results)-len(pending)} confirmed · {len(pending)} to inspect · {unrun} not recognized** in this scope.")
    if not results:
        st.info("No predictions to review for this selection. Run recognition first.")
        next_step("Recognize these fields",NAV[6])
    else:
        only_pending = st.checkbox("Show only unconfirmed fields",value=True)
        choices = pending if only_pending else results
        if not choices:
            st.success("All recognized fields in this scope are confirmed.")
        else:
            ids = [r['image_id'] for r in choices]
            if st.session_state.get('review_item') not in ids:
                st.session_state.pop('review_item',None)
            selected_id = st.selectbox("Field to review",ids,format_func=lambda ident:next(f"{readable(r['source_id'])} — {r['field']}" for r in choices if r['image_id']==ident),key='review_item')
            selected = next(r for r in choices if r['image_id']==selected_id)
            image_col, correction_col = st.columns(2)
            with image_col:
                st.image(selected['crop_path'],caption='Original saved answer')
            with correction_col:
                st.write('**Prediction:**',selected['prediction'] or '(No text recognized)')
                if selected['reason'] or selected['error']:
                    st.warning(selected['reason'] or 'Recognition failed; transcribe the crop manually.')
                    if selected['error']:
                        with st.expander('Recognition error details'):
                            st.code(selected['error'])
                if selected['status']=='FAILED':
                    if st.button('Retry recognition for this field'):
                        item = next(r for r in records if r['image_id']==selected_id)
                        try:
                            with st.spinner('Retrying recognition...'):
                                retried = run([item],IMAGE_BOOK,RESULTS)[0]
                            st.session_state['notice'] = 'Recognition retried. Inspect the new prediction below.' if retried['status']!='FAILED' else 'Recognition is still unavailable for this field. Open its error details or transcribe it manually.'
                            st.rerun()
                        except Exception as exc:
                            recovery('Retry could not finish. Your crops and corrections are retained.',exc)
                answer = st.text_input('Correct text',value=selected['corrected_text'] if selected['corrected_text'] is not None else selected['prediction'],key='correction_'+selected_id)
                if st.button('Save correction and next unconfirmed',type='primary'):
                    correct(RESULTS,selected_id,answer)
                    st.session_state['notice'] = f"Confirmed {selected['field']}. Your correction is saved; regenerate the text workbook to include it."
                    st.session_state.pop('review_item',None)
                    st.rerun()
                if st.button('Flag for later review'):
                    flag(RESULTS,selected_id)
                    st.session_state['notice'] = 'Field flagged for later review.'
                    st.rerun()
    next_step("Prepare current text workbook",NAV[8])

elif section == "Download text":
    st.header("Download the latest text workbook")
    records, results = read(MANIFEST), read(RESULTS)
    active = current_results(records)
    unresolved = len(records)-sum(r.get('review_status')=='CONFIRMED' for r in active)
    st.write(f"The workbook includes **all {len(records)} saved fields across all forms**. {unresolved} fields remain unconfirmed or have not been recognized. Their status is included in Review_Status.")
    fresh, generated = export_state(IMAGE_BOOK,records,results,TEXT_BOOK)
    if generated:
        st.caption(f"Last generated: {generated} (UTC)")
    if TEXT_BOOK.exists() and not fresh:
        st.warning('The existing workbook is out of date or has no freshness record. Regenerate it below to include the latest crops, predictions and corrections.')
    if st.button('Generate latest Text_extraction.xlsx',disabled=not records,type='primary'):
        try:
            export(IMAGE_BOOK,records,results,TEXT_BOOK)
            fresh, generated = export_state(IMAGE_BOOK,records,results,TEXT_BOOK)
            st.success('Workbook generated from the latest saved data, including your corrections.')
            st.caption(f'Generated: {generated} (UTC)')
        except Exception as exc:
            fresh = False
            recovery('Could not create the text workbook. Close Text_extraction.xlsx in Excel and retry. If the image workbook was modified, restore its matching extraction data.',exc)
    if fresh:
        st.download_button('Download latest Text_extraction.xlsx',TEXT_BOOK.read_bytes(),file_name='Text_extraction.xlsx')
    elif not records:
        st.info('Start by choosing a form and extracting its fields.')
        next_step('Choose a form',NAV[1])
