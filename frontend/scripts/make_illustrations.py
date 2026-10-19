"""Generate BB HR's original line-art illustrations (public/illustrations/*.svg).

Run: python3 scripts/make_illustrations.py
Style: 1.5px dark outlines, brand-blue / light-blue fills, orange accents, soft background blobs.
Everything here is drawn from scratch - no third-party artwork.
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "public" / "illustrations"

INK = "#263238"
BLUE = "#048EFF"
BLUE_D = "#0277D6"
LIGHT = "#A8D5FF"
PALE = "#D3EAFF"
BG = "#EAF5FF"
ORANGE = "#F2A23A"
ORANGE_L = "#FCD9A8"
SKIN = "#F1B78E"
SKIN_D = "#C98B62"
WHITE = "#FFFFFF"
GREEN = "#2E9E5B"
RED = "#E21B22"
SW = 1.5  # outline width


def attrs(**kw):
	return " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items() if v is not None)


def shape(tag, fill=WHITE, stroke=INK, sw=SW, **kw):
	return f"<{tag} {attrs(fill=fill, stroke=stroke, stroke_width=sw if stroke != 'none' else None, stroke_linejoin='round', stroke_linecap='round', **kw)}/>"


def path(d, fill=WHITE, stroke=INK, sw=SW):
	return shape("path", fill=fill, stroke=stroke, sw=sw, d=d)


def rect(x, y, w, h, rx=0, fill=WHITE, stroke=INK, sw=SW):
	return shape("rect", fill=fill, stroke=stroke, sw=sw, x=x, y=y, width=w, height=h, rx=rx)


def circle(cx, cy, r, fill=WHITE, stroke=INK, sw=SW):
	return shape("circle", fill=fill, stroke=stroke, sw=sw, cx=cx, cy=cy, r=r)


def line(x1, y1, x2, y2, stroke=INK, sw=SW):
	return shape("line", fill="none", stroke=stroke, sw=sw, x1=x1, y1=y1, x2=x2, y2=y2)


def limb(points, color, width=7):
	"""Thick outlined limb: dark stroke underneath, colour stroke on top."""
	d = "M" + " L".join(f"{x},{y}" for x, y in points)
	return (
		f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{width + 3}" stroke-linecap="round" stroke-linejoin="round"/>'
		f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'
	)


# ---------------------------------------------------------------- scenery
def backdrop(w=240, h=180, blobs=((120, 92, 92, 70),)):
	out = []
	for cx, cy, rx, ry in blobs:
		out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{BG}"/>')
	return "".join(out)


def ground(x1, x2, y):
	return f'<ellipse cx="{(x1 + x2) / 2}" cy="{y + 2}" rx="{(x2 - x1) / 2}" ry="4" fill="{PALE}"/>'


def plant(x, y, s=1.0, color=BLUE):
	"""Potted plant / leafy sprig standing on (x, y)."""
	l = lambda dx, dy, rot: (
		f'<ellipse cx="{x + dx * s}" cy="{y + dy * s}" rx="{4 * s}" ry="{10 * s}" transform="rotate({rot} {x + dx * s} {y + dy * s})" '
		f'fill="{color}" stroke="{INK}" stroke-width="{SW}"/>'
	)
	stem = line(x, y - 4 * s, x, y - 30 * s)
	pot = path(f"M{x - 7 * s},{y - 9 * s} h{14 * s} l-2,{9 * s} h{-10 * s} z", fill=ORANGE)
	return stem + l(-6, -22, -35) + l(6, -26, 35) + l(-5, -36, -20) + l(5, -38, 25) + pot


def sparkle(x, y, s=4, color=ORANGE):
	return path(f"M{x},{y - s} L{x + s * 0.3},{y - s * 0.3} L{x + s},{y} L{x + s * 0.3},{y + s * 0.3} L{x},{y + s} L{x - s * 0.3},{y + s * 0.3} L{x - s},{y} L{x - s * 0.3},{y - s * 0.3} Z", fill=color, sw=1)


# ----------------------------------------------------------------- person
def person(x, g, shirt=BLUE, pants=INK, hair="bob", skin=SKIN, arms=None, legs="stand", flip=False, accessory=""):
	"""Standing person with feet on ground line g, centred on x.

	arms: list of two point lists [(elbow), (hand)] relative to x/g, for left and right arm.
	"""
	s = -1 if flip else 1
	X = lambda dx: x + s * dx
	parts = []
	# legs
	if legs == "stand":
		parts.append(limb([(X(-5), g - 46), (X(-6), g - 24), (X(-7), g - 4)], pants, 8))
		parts.append(limb([(X(5), g - 46), (X(6), g - 24), (X(8), g - 4)], pants, 8))
	elif legs == "walk":
		parts.append(limb([(X(-4), g - 46), (X(-10), g - 24), (X(-16), g - 4)], pants, 8))
		parts.append(limb([(X(4), g - 46), (X(8), g - 24), (X(12), g - 4)], pants, 8))
	feet = [(-8, g - 2), (9, g - 2)] if legs == "stand" else [(-17, g - 2), (13, g - 2)]
	for fx, fy in feet:
		parts.append(f'<ellipse cx="{X(fx) + s * 3}" cy="{fy}" rx="6" ry="3" fill="{INK}"/>')
	# back arm first
	arms = arms or [[(-14, 58), (-14, 38)], [(14, 58), (14, 38)]]
	def arm(pts, sx):
		pp = [(X(sx), g - 78)] + [(X(dx), g - dy) for dx, dy in pts]
		hand = pp[-1]
		return limb(pp[1:], skin, 6) + limb(pp[:2], shirt, 9) + circle(hand[0], hand[1], 3.8, fill=skin, sw=1.2)
	parts.append(arm(arms[1], 10))
	# torso
	parts.append(path(f"M{X(-13)},{g - 73} Q{X(-13)},{g - 83} {X(-5)},{g - 83} L{X(5)},{g - 83} Q{X(13)},{g - 83} {X(13)},{g - 73} L{X(11)},{g - 44} L{X(-11)},{g - 44} Z", fill=shirt))
	parts.append(path(f"M{X(-3)},{g - 82} L{X(0)},{g - 77} L{X(3)},{g - 82}", fill="none", sw=1.2))
	# neck + head
	parts.append(rect(x - 2.5, g - 88, 5, 7, fill=skin, sw=1.2))
	hy = g - 95
	if hair == "long":
		# hangs down the back only, so the face side stays clear
		parts.append(path(f"M{X(-9)},{hy - 4} Q{X(-15)},{hy + 8} {X(-12)},{hy + 20} Q{X(-6)},{hy + 22} {X(-2)},{hy + 16} L{X(-1)},{hy + 4} Z", fill=INK))
	parts.append(circle(x, hy, 9, fill=skin))
	if hair == "bob":
		parts.append(path(f"M{X(-9.5)},{hy + 2} Q{X(-11)},{hy - 12} {X(0)},{hy - 11} Q{X(11)},{hy - 11} {X(9.5)},{hy + 1} Q{X(4)},{hy - 6} {X(-3)},{hy - 5} Q{X(-6)},{hy - 2} {X(-9.5)},{hy + 2} Z", fill=INK))
	elif hair == "bun":
		parts.append(circle(X(-6), hy - 10, 4.5, fill=INK))
		parts.append(path(f"M{X(-9.5)},{hy + 1} Q{X(-10)},{hy - 11} {X(0)},{hy - 10} Q{X(10)},{hy - 10} {X(9.5)},{hy} Q{X(2)},{hy - 5} {X(-9.5)},{hy + 1} Z", fill=INK))
	elif hair == "short":
		parts.append(path(f"M{X(-9.5)},{hy - 1} Q{X(-9)},{hy - 12} {X(1)},{hy - 11} Q{X(11)},{hy - 10} {X(9.5)},{hy - 2} Q{X(5)},{hy - 6} {X(-2)},{hy - 6} Q{X(-6)},{hy - 5} {X(-9.5)},{hy - 1} Z", fill=INK))
	elif hair == "long":
		parts.append(path(f"M{X(-9.5)},{hy + 1} Q{X(-10)},{hy - 11} {X(0)},{hy - 10} Q{X(10)},{hy - 10} {X(9.5)},{hy + 1} Q{X(3)},{hy - 5} {X(-9.5)},{hy + 1} Z", fill=INK))
	# face
	parts.append(circle(X(3.5), hy + 1, 0.9, fill=INK, stroke="none"))
	parts.append(path(f"M{X(2)},{hy + 5} Q{X(4)},{hy + 6.5} {X(6)},{hy + 4.5}", fill="none", sw=1))
	parts.append(accessory)
	# front arm last
	parts.append(arm(arms[0], -10))
	return "".join(parts)


def svg(body):
	# scenes are drawn on a 240x180 canvas; the viewBox trims the empty margin so they read larger in small tiles
	return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="16 10 212 156" fill="none">{body}</svg>'


# ----------------------------------------------------------------- scenes
def checkin():
	b = backdrop(blobs=((128, 90, 96, 72),))
	b += ground(30, 210, 158)
	b += plant(206, 158, 0.9)
	# big phone
	b += rect(118, 22, 70, 128, rx=12, fill=WHITE)
	b += rect(125, 34, 56, 100, rx=5, fill=PALE)
	b += rect(144, 27, 18, 3, rx=1.5, fill=INK, stroke="none")
	for r in (8, 14, 20):
		b += path(f"M{153 - r},{86} a{r},{r} 0 0 1 {2 * r},0", fill="none", stroke=BLUE, sw=2.2)
	b += line(153, 86, 153, 100, stroke=BLUE, sw=2.2)
	b += path("M139,92 v10 M167,92 v8", fill="none", stroke=BLUE, sw=2.2)
	b += circle(178, 40, 11, fill=GREEN)
	b += path("M172,40 l4,4 l8,-8", fill="none", stroke=WHITE, sw=2.4)
	b += rect(133, 112, 40, 10, rx=5, fill=BLUE)
	b += person(82, 158, shirt=ORANGE, hair="bun", arms=[[(-18, 62), (-6, 50)], [(22, 66), (38, 70)]])
	b += sparkle(40, 40) + sparkle(205, 72, 3, BLUE)
	return svg(b)


def attendance():
	b = backdrop(blobs=((120, 92, 100, 70),))
	b += ground(28, 214, 158)
	# calendar board
	b += rect(88, 20, 118, 100, rx=8, fill=WHITE)
	b += path("M88,28 a8,8 0 0 1 8,-8 h102 a8,8 0 0 1 8,8 v12 h-118 z", fill=BLUE)
	for x in (108, 186):
		b += rect(x - 2, 14, 4, 12, rx=2, fill=INK, stroke="none")
	cols = [98, 118, 138, 158, 178]
	rows = [52, 72, 92]
	marks = {(0, 0): "ok", (1, 0): "ok", (2, 0): "ok", (3, 0): "x", (4, 0): "ok", (0, 1): "ok", (1, 1): "leave", (2, 1): "ok"}
	for ri, y in enumerate(rows):
		for ci, x in enumerate(cols):
			m = marks.get((ci, ri))
			fill = {"ok": "#E3F3E8", "x": "#FDE3E4", "leave": ORANGE_L}.get(m, BG)
			b += rect(x, y, 16, 14, rx=3, fill=fill, sw=1.1)
			if m == "ok":
				b += path(f"M{x + 4},{y + 7} l3,3 l6,-6", fill="none", stroke=GREEN, sw=1.8)
			elif m == "x":
				b += path(f"M{x + 5},{y + 4} l6,6 M{x + 11},{y + 4} l-6,6", fill="none", stroke=RED, sw=1.8)
	b += person(62, 158, shirt=BLUE, hair="short", arms=[[(-18, 66), (-24, 50)], [(22, 70), (32, 84)]],
	            accessory=rect(88, 72, 3, 16, rx=1.5, fill=ORANGE, sw=1))
	b += plant(214, 158, 0.85, LIGHT)
	b += sparkle(30, 34)
	return svg(b)


def salary():
	b = backdrop(blobs=((122, 94, 98, 70),))
	b += ground(26, 214, 158)
	# wallet
	b += rect(120, 70, 86, 62, rx=10, fill=BLUE)
	b += rect(116, 62, 74, 18, rx=6, fill=LIGHT)
	b += rect(176, 88, 34, 22, rx=7, fill=BLUE_D)
	b += circle(188, 99, 4, fill=ORANGE)
	# notes sticking out
	b += rect(126, 50, 62, 26, rx=3, fill="#E3F3E8")
	b += circle(157, 63, 7, fill="#C6EAD3")
	b += f'<text x="157" y="67" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" font-weight="700" fill="{GREEN}">₹</text>'
	# coins
	for i, (cx, cy) in enumerate([(206, 146), (196, 150), (214, 152)]):
		b += f'<ellipse cx="{cx}" cy="{cy}" rx="9" ry="4" fill="{ORANGE}" stroke="{INK}" stroke-width="{SW}"/>'
	b += person(78, 158, shirt=ORANGE, hair="long", arms=[[(-16, 64), (-4, 76)], [(24, 70), (40, 84)]],
	            accessory=rect(60, 70, 26, 14, rx=2, fill="#E3F3E8", sw=1.2))
	b += sparkle(46, 36) + sparkle(110, 30, 3, BLUE)
	return svg(b)


def holiday():
	b = backdrop(blobs=((120, 96, 100, 66),))
	b += circle(196, 40, 16, fill=ORANGE_L, stroke="none") + circle(196, 40, 11, fill=ORANGE, stroke="none")
	b += f'<path d="M20,160 Q120,146 222,160 Z" fill="{ORANGE_L}"/>'
	# palm
	b += path("M162,158 Q158,118 170,84", fill="none", stroke=INK, sw=5) + path("M162,158 Q158,118 170,84", fill="none", stroke="#B9734F", sw=3)
	for d in ("M170,84 q-26,-10 -40,8 q20,-4 40,-8", "M170,84 q26,-14 40,4 q-22,-6 -40,-4", "M170,84 q-8,-24 -28,-26 q16,8 28,26", "M170,84 q14,-22 34,-18 q-20,2 -34,18"):
		b += path(d, fill=GREEN)
	# suitcase
	b += rect(108, 120, 30, 36, rx=5, fill=BLUE)
	b += path("M116,120 v-8 h14 v8", fill="none", sw=2)
	b += line(116, 128, 116, 150, stroke=LIGHT, sw=2) + line(130, 128, 130, 150, stroke=LIGHT, sw=2)
	b += person(74, 158, shirt=ORANGE, pants=BLUE, hair="bob", arms=[[(-18, 70), (-26, 96)], [(20, 72), (34, 46)]],
	            accessory=path("M60,58 q14,-10 28,0 l-3,4 h-22 z", fill=LIGHT))
	b += sparkle(36, 40) + sparkle(120, 26, 3, BLUE)
	return svg(b)


def contact_card(x, y, hair, shirt):
	c = rect(x, y, 52, 30, rx=5, fill=WHITE)
	c += circle(x + 12, y + 15, 8, fill=PALE, sw=1.2) + circle(x + 12, y + 13, 3.5, fill=SKIN, sw=1) + path(f"M{x + 6},{y + 21} q6,-6 12,0", fill=shirt, sw=1)
	c += rect(x + 24, y + 9, 22, 3.5, rx=1.7, fill=LIGHT, stroke="none") + rect(x + 24, y + 17, 16, 3.5, rx=1.7, fill=PALE, stroke="none")
	return c


def directory():
	b = backdrop(blobs=((126, 90, 98, 72),))
	b += ground(30, 214, 158)
	b += contact_card(132, 28, "bob", ORANGE) + contact_card(150, 66, "short", BLUE) + contact_card(126, 104, "bun", ORANGE)
	b += person(78, 158, shirt=BLUE, hair="bob", arms=[[(-18, 68), (-4, 88)], [(22, 70), (40, 92)]],
	            accessory=circle(124, 66, 13, fill=WHITE, sw=2.5) + line(114, 76, 104, 86, sw=3.5))
	b += plant(214, 158, 0.85)
	b += sparkle(40, 38)
	return svg(b)


def team():
	b = backdrop(blobs=((120, 90, 104, 70),))
	b += ground(22, 218, 158)
	b += person(74, 158, shirt=ORANGE, hair="long", arms=[[(-16, 60), (-14, 40)], [(18, 70), (30, 88)]])
	b += person(166, 158, shirt=LIGHT, hair="short", flip=True, arms=[[(-16, 60), (-14, 40)], [(18, 70), (30, 88)]])
	b += person(120, 160, shirt=BLUE, hair="bun", arms=[[(-20, 70), (-34, 84)], [(20, 70), (34, 84)]])
	b += sparkle(36, 36) + sparkle(206, 44, 3, BLUE) + sparkle(120, 22, 3)
	return svg(b)


def alert():
	b = backdrop(blobs=((122, 92, 96, 70),))
	b += ground(30, 214, 158)
	b += path("M150,26 L206,128 L94,128 Z", fill=ORANGE_L)
	b += path("M150,44 L192,120 L108,120 Z", fill=ORANGE)
	b += rect(146, 68, 8, 30, rx=4, fill=WHITE) + circle(150, 108, 4.5, fill=WHITE)
	b += person(70, 158, shirt=BLUE, hair="bob", arms=[[(-16, 66), (-4, 86)], [(20, 70), (32, 84)]])
	b += path("M44,52 q-6,-12 4,-16 q10,-2 8,10 q-2,6 -6,8", fill="none", sw=2) + circle(50, 64, 1.8, fill=INK, stroke="none")
	b += plant(212, 158, 0.8, LIGHT)
	return svg(b)


def chart():
	b = backdrop(blobs=((122, 90, 100, 70),))
	b += ground(28, 216, 158)
	b += rect(98, 22, 112, 84, rx=6, fill=WHITE)
	b += line(154, 106, 140, 154, sw=2.5) + line(154, 106, 168, 154, sw=2.5)
	for i, (h, c) in enumerate([(26, LIGHT), (44, BLUE), (34, ORANGE), (56, BLUE)]):
		x = 112 + i * 22
		b += rect(x, 96 - h, 14, h, rx=2, fill=c, sw=1.2)
	b += path("M110,58 L134,44 L156,52 L190,28", fill="none", stroke=ORANGE, sw=2.2)
	b += circle(190, 28, 3, fill=ORANGE)
	b += person(68, 158, shirt=ORANGE, hair="short", arms=[[(-16, 66), (-6, 84)], [(20, 74), (34, 96)]])
	b += sparkle(36, 34)
	return svg(b)


def profile():
	b = backdrop(blobs=((122, 90, 100, 70),))
	b += ground(28, 214, 158)
	b += rect(110, 24, 92, 118, rx=10, fill=WHITE)
	b += path("M110,34 a10,10 0 0 1 10,-10 h72 a10,10 0 0 1 10,10 v16 h-92 z", fill=BLUE)
	b += circle(156, 66, 18, fill=PALE) + circle(156, 61, 7, fill=SKIN, sw=1.2)
	b += path("M150,57 q6,-8 12,0 q-2,-7 -6,-7 q-4,0 -6,7 z", fill=INK, sw=1)
	b += path("M144,80 q12,-14 24,0", fill=ORANGE, sw=1.2)
	for i, wdt in enumerate((60, 44, 52)):
		b += rect(126, 96 + i * 12, wdt, 5, rx=2.5, fill=PALE if i else LIGHT, stroke="none")
	b += person(74, 158, shirt=BLUE, hair="long", arms=[[(-16, 66), (-10, 46)], [(22, 72), (38, 86)]])
	b += plant(214, 158, 0.8)
	b += sparkle(40, 36)
	return svg(b)


def empty():
	b = backdrop(blobs=((120, 92, 92, 66),))
	b += ground(36, 204, 158)
	b += rect(92, 30, 70, 92, rx=8, fill=WHITE)
	b += rect(110, 24, 34, 14, rx=4, fill=LIGHT)
	for i in range(3):
		b += rect(104, 54 + i * 16, 46, 6, rx=3, fill=BG, stroke="none")
	b += person(178, 158, shirt=ORANGE, hair="short", flip=True, arms=[[(-22, 74), (-34, 70)], [(22, 74), (34, 70)]])
	b += sparkle(70, 34) + sparkle(160, 24, 3, BLUE) + sparkle(60, 120, 3, BLUE)
	return svg(b)


def login():
	b = backdrop(blobs=((124, 92, 100, 70),))
	b += ground(26, 218, 158)
	b += rect(102, 54, 98, 64, rx=6, fill=WHITE)
	b += rect(109, 61, 84, 50, rx=3, fill=PALE)
	b += path("M92,118 h118 l-8,12 h-102 z", fill=BLUE)
	b += rect(124, 74, 54, 8, rx=4, fill=WHITE, sw=1.2) + rect(124, 88, 54, 8, rx=4, fill=WHITE, sw=1.2)
	b += circle(196, 46, 15, fill=ORANGE)
	b += rect(189, 45, 14, 10, rx=2, fill=WHITE, sw=1.2) + path("M192,45 v-3 a4,4 0 0 1 8,0 v3", fill="none", sw=1.4)
	b += person(70, 158, shirt=ORANGE, hair="bun", arms=[[(-16, 66), (-8, 84)], [(22, 74), (36, 76)]])
	b += sparkle(36, 40) + sparkle(116, 30, 3, BLUE)
	return svg(b)


def leave():
	b = backdrop(blobs=((120, 92, 100, 68),))
	b += ground(26, 214, 158)
	b += rect(118, 34, 82, 74, rx=8, fill=WHITE)
	b += path("M118,42 a8,8 0 0 1 8,-8 h66 a8,8 0 0 1 8,8 v10 h-82 z", fill=ORANGE)
	b += f'<text x="159" y="88" text-anchor="middle" font-family="Arial, sans-serif" font-size="26" font-weight="700" fill="{BLUE}">OFF</text>'
	b += person(74, 158, shirt=BLUE, hair="long", arms=[[(-16, 66), (-8, 80)], [(22, 72), (30, 80)]],
	            accessory=rect(78, 72, 12, 12, rx=2, fill=WHITE, sw=1.2) + path("M90,75 q5,0 5,4 q0,4 -5,4", fill="none", sw=1.2) + path("M81,68 q2,-4 0,-7 M86,68 q2,-4 0,-7", fill="none", stroke=LIGHT, sw=1.4))
	b += plant(212, 158, 0.85)
	b += sparkle(36, 36)
	return svg(b)


SCENES = {
	"checkin": checkin, "attendance": attendance, "salary": salary, "holiday": holiday, "directory": directory,
	"team": team, "alert": alert, "chart": chart, "profile": profile, "empty": empty, "login": login, "leave": leave,
}

if __name__ == "__main__":
	OUT.mkdir(parents=True, exist_ok=True)
	for name, fn in SCENES.items():
		(OUT / f"{name}.svg").write_text(fn())
	print(f"wrote {len(SCENES)} illustrations to {OUT}")
