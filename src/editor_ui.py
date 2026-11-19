"""Guided drawing editor with recoverable drafts and keyboard alternatives."""
import uuid
import streamlit as st
from .canvas import select_regions
from .region_selector import normalize_box, crop
from .editor_state import draft_path, load_draft, update_draft, undo_draft, is_dirty


def edit_fields(form, page, layout, original, shown, existing):
    initial = []
    for i, field in enumerate((existing or {}).get('fields', [])):
        if field['page'] != page:
            continue
        x1,y1,x2,y2 = field['box']
        initial.append({'id': f'saved_{page}_{i}', 'name':field['name'], 'mode':field['mode'],
                        'left':x1*shown.width, 'top':y1*shown.height,
                        'width':(x2-x1)*shown.width, 'height':(y2-y1)*shown.height})
    path = draft_path(form, page, layout)
    state = load_draft(path, initial)
    revision_key = 'editor_revision_' + path.stem
    revision = st.session_state.get(revision_key, 0)
    namespace = f'{path.stem}_{revision}'

    def reload_editor():
        st.session_state[revision_key] = revision + 1
        st.rerun()

    st.caption('Draft autosaves as you edit (text saves when you press Enter or leave the input). Unextracted changes remain available when you return to this form and drawing mode.')
    left, right = st.columns([3,2], gap='large')
    with left:
        st.subheader('Draw around the answers')
        st.write('Hold the left mouse button and drag from one corner of an answer to the opposite corner. Release to create a numbered box.')
        st.caption('Drag inside to move. Use the bottom-right handle to resize. Delete a box with its × button; Undo restores the previous edit.')
        objects = select_regions(shown, state['regions'], namespace)
        controls = st.columns(2)
        if controls[0].button('Undo last edit', disabled=not state['history'], key=f'undo_{namespace}'):
            undo_draft(path)
            reload_editor()
        if controls[1].button('Add box using keyboard', key=f'add_{namespace}', help='Creates a box in the centre. Use its position controls on the right to move and resize it.'):
            regions = state['regions'] + [{'id':uuid.uuid4().hex, 'name':'', 'mode':'handwritten', 'left':shown.width*.25, 'top':shown.height*.25, 'width':shown.width*.5, 'height':shown.height*.15}]
            update_draft(path, state, regions)
            reload_editor()
        st.caption('Keyboard workflow: Tab to Add box using keyboard, press Enter, then use the Position and size controls for that box. Drawing with the mouse remains available.')
    fields, regions = [], []
    old_by_id = {r['id']:r for r in state['regions']}
    with right:
        st.subheader('Name each numbered box')
        if not objects:
            st.info('Draw your first box, or use Add box using keyboard. Its name and crop preview will appear here.')
        for i, obj in enumerate(objects):
            identity = obj.get('id',f'box_{i}')
            old = old_by_id.get(identity, obj)
            st.markdown(f'**Box {i+1}**')
            name = st.text_input(f'Column name for box {i+1}', value=old.get('name',''), placeholder='e.g. Name or Date', key=f'name_{namespace}_{identity}')
            modes = ['handwritten','printed','auto']
            mode = st.selectbox(f'Writing in box {i+1}', modes, index=modes.index(old.get('mode','handwritten')), format_func=lambda m:{'handwritten':'Handwritten','printed':'Printed / typed','auto':'Unknown (requires review)'}[m], key=f'mode_{namespace}_{identity}')
            region = dict(obj, id=identity, name=name.strip(), mode=mode)
            regions.append(region)
            try:
                box = normalize_box(obj, shown.width, shown.height)
                st.image(crop(original,box), caption=f'Crop from box {i+1}', width='stretch')
                fields.append({'name':name.strip(),'page':page,'box':box,'mode':mode})
            except ValueError:
                st.error('Keep the whole box inside the page and give it a positive width and height.')
            with st.expander(f'Position and size for box {i+1} (keyboard accessible)'):
                st.caption('Values use preview pixels. Top-left is 0, 0. Tab between inputs; arrow keys adjust values. Apply updates the box and preview.')
                with st.form(f'position_{namespace}_{identity}'):
                    x = st.number_input('Left', 0.0, float(shown.width-1), min(float(shown.width-1),float(obj['left'])), key=f'x_{namespace}_{identity}')
                    y = st.number_input('Top', 0.0, float(shown.height-1), min(float(shown.height-1),float(obj['top'])), key=f'y_{namespace}_{identity}')
                    w = st.number_input('Width', 1.0, float(shown.width), max(1.,float(obj['width'])), key=f'w_{namespace}_{identity}')
                    h = st.number_input('Height', 1.0, float(shown.height), max(1.,float(obj['height'])), key=f'h_{namespace}_{identity}')
                    if st.form_submit_button('Apply position and size'):
                        if x+w > shown.width or y+h > shown.height:
                            st.error('This box extends beyond the page. Reduce its position or size.')
                        else:
                            # Capture current drawing, including new fields, before replacing this region.
                            updated = [dict(o, **{k: old_by_id.get(o.get('id'),o).get(k, '' if k=='name' else 'handwritten') for k in ('name','mode')}) for o in objects]
                            updated[i] = dict(region,left=x,top=y,width=w,height=h)
                            update_draft(path,state,updated)
                            reload_editor()
            if st.button(f'Remove box {i+1}', key=f'remove_{namespace}_{identity}'):
                update_draft(path,state,[dict(o, name=old_by_id.get(o.get('id'),o).get('name',''), mode=old_by_id.get(o.get('id'),o).get('mode','handwritten')) for j,o in enumerate(objects) if j!=i])
                reload_editor()
        state = update_draft(path,state,regions)
        st.caption('Draft saved locally. Changes are not yet extracted.' if is_dirty(state) else 'These fields match the last extraction from this editor.')
        names = [f['name'] for f in fields]
        ready = bool(fields) and len(fields)==len(objects) and all(names) and len(names)==len(set(names)) and 'Source_Form_ID' not in names
        if 'Source_Form_ID' in names:
            st.warning('Source_Form_ID is reserved for tracing each form. Choose another column name.')
        elif fields and not ready:
            st.warning('Give every box a nonempty, unique column name before extracting.')
    return fields, ready, path
