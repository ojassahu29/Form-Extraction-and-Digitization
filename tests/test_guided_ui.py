from pathlib import Path
from PIL import Image


def test_keyboard_editor_to_current_export(tmp_path, monkeypatch):
    """Exercise UI transitions without network, browser gestures or production data."""
    from streamlit.testing.v1 import AppTest
    import src.config as cfg
    import src.editor_ui as editor
    import src.editor_state as drafts
    import src.form_regions as regions
    import src.image_extractor as extractor
    import src.template_manager as templates
    from src.manifest_manager import read, write
    paths = {'INPUT':'input','CROPS':'crops','OUTPUT':'output','MANIFESTS':'manifests','TEMPLATES':'templates',
             'IMAGE_BOOK':'output/Image_extract.xlsx','TEXT_BOOK':'output/Text_extraction.xlsx',
             'MANIFEST':'manifests/crops.json','RESULTS':'manifests/results.json'}
    for key,relative in paths.items():
        monkeypatch.setattr(cfg,key,tmp_path/relative)
    cfg.ensure_dirs()
    form = cfg.INPUT/'example.png'
    Image.new('RGB',(400,200),'white').save(form)
    original_draft_path = drafts.draft_path
    monkeypatch.setattr(editor,'draft_path',lambda f,p,l:original_draft_path(f,p,l,cfg.MANIFESTS))
    original_load,original_save = regions.load_regions,regions.save_regions
    monkeypatch.setattr(regions,'load_regions',lambda f:original_load(f,cfg.MANIFESTS))
    monkeypatch.setattr(regions,'save_regions',lambda f,fields,w,h:original_save(f,fields,w,h,cfg.MANIFESTS))
    monkeypatch.setattr(templates,'TEMPLATES',cfg.TEMPLATES)
    original_process=extractor.process
    monkeypatch.setattr(extractor,'process',lambda f,t,force=False:original_process(f,t,force=force,image_book=cfg.IMAGE_BOOK,manifest_path=cfg.MANIFEST,crop_dir=cfg.CROPS,input_dir=cfg.INPUT))
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=30).run()
    assert not app.exception
    assert app.sidebar.radio[0].options == ['Choose forms','Mark & extract','Check images','Text workspace']
    app.sidebar.radio[0].set_value('Mark & extract').run()
    next(b for b in app.button if b.label=='Add box using keyboard').click().run()
    assert not app.exception
    next(t for t in app.text_input if t.label=='Column name for box 1').set_value('Name').run()
    assert any('Draft' in c.value for c in app.caption)
    next(b for b in app.button if b.label=='Save fields and extract this form').click().run()
    assert not app.exception
    assert app.header[0].value=='Check the cropped answers'
    assert len(read(cfg.MANIFEST))==1
    next(b for b in app.button if b.label=='Recognize these images').click().run()
    assert not app.exception
    assert next(r for r in app.radio if r.label=='Text workflow').value=='Recognize text'
    # Supply a labelled mock prediction; real model loading is outside this UI test.
    row=read(cfg.MANIFEST)[0]
    write(cfg.RESULTS,[dict(row,prediction='Alic',corrected_text=None,status='NEEDS_REVIEW',review_status='PENDING',reason='mock',error='',model='mock')])
    next(r for r in app.radio if r.label=='Text workflow').set_value('Review & correct').run()
    next(t for t in app.text_input if t.label=='Correct text').set_value('Alice').run()
    next(b for b in app.button if b.label=='Save correction and next unconfirmed').click().run()
    assert not app.exception
    assert any('All recognized fields' in x.value for x in app.success)
    next(b for b in app.button if b.label=='Prepare current text workbook').click().run()
    assert not app.exception
    next(b for b in app.button if b.label=='Generate latest Text_extraction.xlsx').click().run()
    assert not app.exception
    from openpyxl import load_workbook
    assert load_workbook(cfg.TEXT_BOOK).active['B2'].value=='Alice'
    result=read(cfg.RESULTS);result[0]['corrected_text']='Asha';write(cfg.RESULTS,result)
    app.run()
    assert any('out of date' in w.value for w in app.warning)
