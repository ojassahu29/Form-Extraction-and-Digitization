"""Create a non-sensitive printed sample form for UI and mapping demonstration."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 35) if Path("C:/Windows/Fonts/arial.ttf").exists() else ImageFont.load_default()
hand_font = ImageFont.truetype("C:/Windows/Fonts/segoepr.ttf", 43) if Path("C:/Windows/Fonts/segoepr.ttf").exists() else font
for filename, values in [("sample_form.png", ("Asha Rao", "2026B4A123", "09-11-2026")), ("sample_form_2.png", ("Ravi Sen", "2026B4A124", "10-11-2026"))]:
    dest = Path(__file__).with_name(filename)
    image = Image.new("RGB", (1200, 800), "white")
    d = ImageDraw.Draw(image)
    for (y, label), value in zip([(120, "Name"), (300, "Roll Number"), (480, "Date")], values):
        d.text((70, y), label, fill="black", font=font)
        d.rectangle((350, y-10, 1090, y+85), outline="black", width=3)
        d.text((380, y+5), value, fill="black", font=hand_font)
    image.save(dest)
    print(dest)
