from PIL import Image
from src.form_regions import save_regions, load_regions
from src.image_extractor import process
from src.manifest_manager import read
from src.excel_manager import validate_workbook

def test_individual_regions_and_replacement(tmp_path):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    Image.new("RGB", (200, 100), "white").save(a)
    Image.new("RGB", (200, 100), "grey").save(b)
    def field(box):
        return [{"name": "Name", "page": 1, "mode": "handwritten", "box": box}]
    config_a = save_regions(a, field([.1,.1,.4,.4]), 200, 100, tmp_path)
    config_b = save_regions(b, field([.5,.5,.9,.9]), 200, 100, tmp_path)
    assert load_regions(a, tmp_path) == config_a
    assert load_regions(b, tmp_path) == config_b
    assert config_a['fields'] != config_b['fields']
    options = dict(image_book=tmp_path/'images.xlsx', manifest_path=tmp_path/'crops.json', crop_dir=tmp_path/'crops', input_dir=tmp_path/'input')
    assert process([a], config_a, **options)[0][1] == 'PROCESSED'
    assert process([b], config_b, **options)[0][1] == 'PROCESSED'
    before = read(options['manifest_path'])
    config_a = save_regions(a, field([.2,.2,.6,.6]), 200, 100, tmp_path)
    assert process([a], config_a, force=True, **options)[0][1] == 'PROCESSED'
    after = read(options['manifest_path'])
    assert len(after) == 2
    old = next(r for r in before if r['template_id']==config_a['name'])
    new = next(r for r in after if r['template_id']==config_a['name'])
    assert old['excel_row'] == new['excel_row']
    assert old['image_id'] != new['image_id']
    assert validate_workbook(options['image_book'], after)
