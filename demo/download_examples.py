"""Download five attributed synthetic forms and prepare manual OCR templates."""
import json
import urllib.request
from pathlib import Path
from PIL import Image
from src.template_manager import save

BASE = "https://huggingface.co/datasets/hyperbots-inc/synthetic-handwritten-forms/resolve/main/"

def main():
    dest = Path(__file__).resolve().parent / "internet_examples"
    dest.mkdir(exist_ok=True)
    raw = urllib.request.urlopen(BASE + "data/test/metadata.jsonl").read()
    records = [json.loads(line) for line in raw.splitlines()][:5]
    summary = []
    for record in records:
        filename = record['file_name']
        target = dest / filename
        if not target.exists():
            target.write_bytes(urllib.request.urlopen(BASE + 'data/test/' + filename).read())
        with Image.open(target) as image:
            image.verify()
        with Image.open(target) as image:
            width, height = image.size
        fields = []
        expected = {}
        for field in record['fields']:
            if not field['handwritten'] or len(fields) >= 3:
                continue
            x1, y1, x2, y2 = field['bbox']
            fields.append({'name': field['label'], 'page': 1, 'mode': 'handwritten', 'box': [max(0,x1-5)/width,max(0,y1-5)/height,min(width,x2+5)/width,min(height,y2+5)/height]})
            expected[field['label']] = field['value']
        name = 'internet_' + record['doc_type']
        save({'name':name,'reference_width':width,'reference_height':height,'reference_page':1,'fields':fields})
        summary.append({'file':filename,'type':record['doc_type'],'template':name,'expected':expected,'source':BASE+'data/test/'+filename})
        print(filename, record['doc_type'], expected)
    (dest/'expected_values.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (dest/'source_metadata.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    print('Saved five forms and templates. See demo/internet_examples/README.md')

if __name__ == '__main__':
    main()
