import io
from PIL import Image
from src.template_preview import layout_png


def test_layout_png_renders_selected_page_only():
    template = {'name':'Example', 'reference_width':1000, 'reference_height':500, 'fields':[
        {'name':'Name','page':1,'box':[.1,.1,.4,.4]},
        {'name':'Date','page':2,'box':[.6,.6,.9,.9]},
    ]}
    png = layout_png(template, 1)
    with Image.open(io.BytesIO(png)) as image:
        assert image.format == 'PNG'
        # Reference page scales to 520 x 260; the border of Name is black.
        assert image.getpixel((24+52,24+26)) == (0,0,0)
        # The page-2 region must not be drawn on page 1.
        assert image.getpixel((24+312,24+156)) == (255,255,255)
