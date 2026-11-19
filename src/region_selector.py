from PIL import Image

def normalize_box(box, width, height):
    x, y, w, h = (float(box[k]) for k in ("left", "top", "width", "height"))
    if width <= 0 or height <= 0 or w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > width + .001 or y + h > height + .001:
        raise ValueError("Region must be a positive rectangle inside the preview")
    return [x / width, y / height, (x + w) / width, (y + h) / height]

def pixel_box(normalized, width, height):
    if len(normalized) != 4 or not (0 <= normalized[0] < normalized[2] <= 1 and 0 <= normalized[1] < normalized[3] <= 1):
        raise ValueError("Invalid normalized rectangle")
    x1 = round(normalized[0] * width)
    y1 = round(normalized[1] * height)
    x2 = round(normalized[2] * width)
    y2 = round(normalized[3] * height)
    if x2 <= x1 or y2 <= y1:
        raise ValueError("Region is too small at this resolution")
    return x1, y1, x2, y2

def crop(image: Image.Image, normalized):
    return image.crop(pixel_box(normalized, *image.size))
