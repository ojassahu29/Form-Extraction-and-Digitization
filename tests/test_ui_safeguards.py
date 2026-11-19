from PIL import Image
from src.editor_state import load_draft, update_draft, undo_draft, mark_extracted, is_dirty
from src.template_manager import save, delete, restore, list_templates
from src.export_manager import export, export_state
from src.image_extractor import process
from src.manifest_manager import read


def test_draft_survives_reopen_and_undo(tmp_path):
    path = tmp_path/'draft.json'
    empty = load_draft(path,[])
    region = {'id':'a','left':1,'top':1,'width':30,'height':10,'name':'Name'}
    state = update_draft(path,empty,[region])
    assert load_draft(path,[])['regions']==[region]
    assert is_dirty(state)
    mark_extracted(path)
    state = load_draft(path,[])
    assert not is_dirty(state)
    update_draft(path,state,[])
    assert undo_draft(path)['regions']==[region]
    assert not is_dirty(load_draft(path,[]))


def test_layout_removal_is_recoverable(tmp_path,monkeypatch):
    import src.template_manager as tm
    monkeypatch.setattr(tm,'TEMPLATES',tmp_path)
    layout={'name':'Example','fields':[{'name':'Name','mode':'handwritten','page':1,'box':[.1,.1,.5,.5]}]}
    save(layout)
    removed=delete('Example')
    assert not list_templates()
    assert removed.exists()
    restore(removed)
    assert list_templates()==['Example']


def test_export_stale_after_correction_or_manifest_change(tmp_path):
    source=tmp_path/'one.png'
    Image.new('RGB',(200,100),'white').save(source)
    manifest=tmp_path/'manifest.json'; book=tmp_path/'images.xlsx'; output=tmp_path/'text.xlsx'
    layout={'name':'Example','fields':[{'name':'Name','mode':'handwritten','page':1,'box':[.1,.1,.5,.5]}]}
    process([source],layout,image_book=book,manifest_path=manifest,crop_dir=tmp_path/'crops',input_dir=tmp_path/'input')
    records=read(manifest)
    result=dict(records[0], prediction='Alic',corrected_text=None,status='NEEDS_REVIEW',review_status='PENDING',reason='',error='',model='mock')
    export(book,records,[result],output)
    assert export_state(book,records,[result],output)[0]
    result['corrected_text']='Alice'
    assert not export_state(book,records,[result],output)[0]
    export(book,records,[result],output)
    assert export_state(book,records,[result],output)[0]
    records[0]['mode']='auto'
    assert not export_state(book,records,[result],output)[0]
