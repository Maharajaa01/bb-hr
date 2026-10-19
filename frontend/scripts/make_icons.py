"""Render the BB HR app icons (PNG) with Pillow. Run: ../../env/bin/python scripts/make_icons.py"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "public" / "icons"
BLUE, WHITE, LIGHT = (4, 142, 255), (255, 255, 255), (168, 213, 255)


def font(size):
	for name in ("DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
		try:
			return ImageFont.truetype(name, size)
		except OSError:
			continue
	return ImageFont.load_default()


def icon(size, maskable=False, rounded=True):
	img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	if maskable or not rounded:
		d.rectangle([0, 0, size, size], fill=BLUE)
	else:
		d.rounded_rectangle([0, 0, size - 1, size - 1], radius=size // 4.5, fill=BLUE)
	# safe zone for maskable icons is the central 80%
	scale = 0.62 if maskable else 0.78
	box = size * scale
	off = (size - box) / 2
	# light-blue bar under the monogram
	d.rounded_rectangle([off + box * 0.18, off + box * 0.78, off + box * 0.82, off + box * 0.86],
	                    radius=box * 0.04, fill=LIGHT)
	f = font(int(box * 0.42))
	text = "BB"
	tw = d.textlength(text, font=f)
	d.text(((size - tw) / 2, off + box * 0.18), text, font=f, fill=WHITE)
	return img


OUT.mkdir(parents=True, exist_ok=True)
icon(192).save(OUT / "icon-192.png")
icon(512).save(OUT / "icon-512.png")
icon(512, maskable=True).save(OUT / "maskable-512.png")
icon(180, rounded=False).convert("RGB").save(OUT / "apple-touch-icon.png")
print("icons written to", OUT)
