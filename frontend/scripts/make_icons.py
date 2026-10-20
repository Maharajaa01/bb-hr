"""Render the BB HRMS app icons (PNG) with Pillow. Run: npm run icons

Mark: brand-blue tile with "BB" over "HRMS" in heavy Poppins (scripts/fonts, SIL OFL - see OFL-Poppins.txt).
Drawn at 4x and downsampled so edges stay crisp at every size.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "public" / "icons"
FONTS = HERE / "fonts"
TOP, BOTTOM, WHITE = (26, 156, 255), (3, 120, 230), (255, 255, 255)
SS = 4  # supersampling factor


def gradient(size):
	"""Vertical brand-blue gradient, slightly lighter at the top."""
	col = Image.new("RGB", (1, size))
	for y in range(size):
		t = y / max(size - 1, 1)
		col.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM)))
	return col.resize((size, size))


def draw_tracked(d, text, font, cx, top, tracking):
	"""Draw text centred on cx with extra letter spacing (Pillow has no tracking option)."""
	widths = [font.getlength(ch) for ch in text]
	x = cx - (sum(widths) + tracking * (len(text) - 1)) / 2
	for ch, w in zip(text, widths):
		d.text((x, top), ch, font=font, fill=WHITE, anchor="ls")
		x += w + tracking


def icon(size, maskable=False, rounded=True, word=True):
	S = size * SS
	tile = gradient(S).convert("RGBA")
	if rounded and not maskable:
		mask = Image.new("L", (S, S), 0)
		ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=S * 0.225, fill=255)
		tile.putalpha(mask)
	d = ImageDraw.Draw(tile)

	# maskable icons may be cropped to a circle: keep the lettering inside the central safe zone
	box = S * (0.60 if maskable else 0.80)
	big = ImageFont.truetype(str(FONTS / "Poppins-Black.ttf"), round(box * 0.50))
	small = ImageFont.truetype(str(FONTS / "Poppins-ExtraBold.ttf"), round(box * 0.205))

	# cap heights (no descenders in either line) for optical vertical centring
	cap_big = -big.getbbox("B", anchor="ls")[1]
	cap_small = -small.getbbox("H", anchor="ls")[1]
	# "HRMS" is unreadable at favicon size, so tiny icons show "BB" alone
	gap = box * 0.10
	block = cap_big + gap + cap_small if word else cap_big
	y0 = (S - block) / 2
	draw_tracked(d, "BB", big, S / 2, y0 + cap_big, tracking=-box * 0.01)
	if word:
		draw_tracked(d, "HRMS", small, S / 2, y0 + cap_big + gap + cap_small, tracking=box * 0.035)

	return tile.resize((size, size), Image.LANCZOS)


OUT.mkdir(parents=True, exist_ok=True)
icon(192).save(OUT / "icon-192.png", optimize=True)
icon(512).save(OUT / "icon-512.png", optimize=True)
icon(512, maskable=True).save(OUT / "maskable-512.png", optimize=True)
icon(180, rounded=False).convert("RGB").save(OUT / "apple-touch-icon.png", optimize=True)
icon(32, word=False).save(OUT / "favicon-32.png", optimize=True)
print("icons written to", OUT)
