"""Black-on-white layout thumbnails; these contain no source-form data."""
import io
from PIL import Image, ImageDraw, ImageFont
from .region_selector import pixel_box


def layout_png(template, page):
    """Render normalized regions at the reference aspect ratio with a field key."""
    fields = [f for f in template['fields'] if int(f['page']) == int(page)]
    ref_width = max(1, int(template.get('reference_width', 800)))
    ref_height = max(1, int(template.get('reference_height', 1100)))
    scale = min(520 / ref_width, 620 / ref_height)
    width, height = max(20, round(ref_width * scale)), max(20, round(ref_height * scale))
    margin = 24
    legend_height = 30 * len(fields) + 55
    image = Image.new('RGB', (max(width + margin * 2, 440), height + margin * 2 + legend_height), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=16)
    draw.rectangle((margin, margin, margin + width, margin + height), outline='black', width=1)
    for i, field in enumerate(fields, 1):
        x1, y1, x2, y2 = pixel_box(field['box'], width, height)
        draw.rectangle((margin+x1, margin+y1, margin+x2, margin+y2), outline='black', width=3)
        label = str(i)
        draw.text((margin+x1+4, margin+y1+2), label, fill='black', font=font)
    y = height + margin * 2
    draw.text((margin, y), f"Page {page} - {len(fields)} fields", fill='black', font=font)
    for i, field in enumerate(fields, 1):
        # Wrap long names rather than place text over the layout rectangles.
        name = field['name']
        if len(name) > 47:
            name = name[:44] + '...'
        draw.text((margin, y + 30*i), f"{i}. {name}", fill='black', font=font)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()
