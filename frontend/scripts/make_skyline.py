"""Generate src/components/illustrations/Skyline.vue - the Chennai skyline hero on the Dashboard.

Gopuram, Chennai Central clock tower, glass towers, palms and the Marina, 480x180.
Run: python3 scripts/make_skyline.py   (edit this script, not the .vue file)
"""
from pathlib import Path

TARGET = Path(__file__).resolve().parent.parent / "src" / "components" / "illustrations" / "Skyline.vue"

W, H, GROUND = 480, 180, 150
out = []
a = out.append


def f(x):
	return f"{x:g}"


def poly(pts, fill, extra=""):
	a(f'<polygon points="{" ".join(f"{f(x)},{f(y)}" for x, y in pts)}" fill="{fill}"{extra}/>')


def rect(x, y, w, h, fill, rx=0, extra=""):
	r = f' rx="{f(rx)}"' if rx else ""
	a(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}"{r} fill="{fill}"{extra}/>')


def arch_window(x, y, w, h, fill, extra=""):
	r = w / 2
	a(f'<path d="M{f(x)} {f(y+h)}V{f(y+r)}a{f(r)} {f(r)} 0 0 1 {f(w)} 0V{f(y+h)}z" fill="{fill}"{extra}/>')


# ---------------------------------------------------------------- defs
a("""<defs>
<linearGradient id="sl-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4FAEFF"/><stop offset=".65" stop-color="#A9D8FF"/><stop offset="1" stop-color="#E4F3FF"/></linearGradient>
<radialGradient id="sl-sun" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FFF4C9" stop-opacity=".9"/><stop offset="1" stop-color="#FFF4C9" stop-opacity="0"/></radialGradient>
<linearGradient id="sl-sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2D9FFF"/><stop offset="1" stop-color="#0670D6"/></linearGradient>
<linearGradient id="sl-g1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2AA2FF"/><stop offset="1" stop-color="#0A78E0"/></linearGradient>
<linearGradient id="sl-g2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6BBDFF"/><stop offset="1" stop-color="#2E95F2"/></linearGradient>
<linearGradient id="sl-g3" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1683E8"/><stop offset="1" stop-color="#0559B0"/></linearGradient>
</defs>""")

# ---------------------------------------------------------------- sky, sun, clouds, birds
rect(0, 0, W, H, "url(#sl-sky)")
a('<circle cx="432" cy="40" r="44" fill="url(#sl-sun)"/>')
a('<circle cx="432" cy="40" r="15" fill="#FFD66B"/>')


def cloud(x, y, s, op=0.95):
	a(f'<g transform="translate({f(x)} {f(y)}) scale({f(s)})" opacity="{op}">'
	  '<path d="M0 14a8 8 0 0 1 8-8 11 11 0 0 1 20-3 9 9 0 0 1 14 7 6 6 0 0 1 2 12H4a6 6 0 0 1-4-8z" fill="#fff"/>'
	  '<path d="M4 22h40a6 6 0 0 0 4-3H2a6 6 0 0 0 2 3z" fill="#DCEEFF"/></g>')


cloud(36, 22, 1.1)
cloud(250, 14, 0.8, 0.9)
cloud(352, 52, 0.6, 0.8)
a('<g fill="none" stroke="#2E5E8C" stroke-width="1.2" stroke-linecap="round" opacity=".55">'
  '<path d="M176 40q3-3 6 0q3-3 6 0"/><path d="M192 32q2.5-2.5 5 0q2.5-2.5 5 0"/><path d="M166 30q2-2 4 0q2-2 4 0"/></g>')

# ---------------------------------------------------------------- far city (haze)
far = [(0, 96, 22), (24, 84, 16), (42, 104, 20), (64, 90, 14), (150, 98, 18), (170, 80, 14), (186, 92, 12),
       (300, 88, 16), (318, 100, 22), (404, 86, 18), (424, 100, 16), (442, 78, 14), (458, 94, 22)]
for x, y, w in far:
	rect(x, y, w, GROUND - y, "#C7E4FF")
# a couple of spires for variety
poly([(170, 80), (177, 70), (184, 80)], "#C7E4FF")
rect(448.5, 66, 1.5, 12, "#C7E4FF")

# ---------------------------------------------------------------- mid city
mid = [(8, 108, 26), (36, 116, 20), (176, 104, 22), (292, 110, 22), (408, 106, 24), (434, 116, 20), (456, 102, 24)]
for x, y, w in mid:
	rect(x, y, w, GROUND - y, "#9CCFFF")
	rect(x + w * 0.62, y, w * 0.38, GROUND - y, "#8CC5FA")
	for wy in range(int(y) + 6, GROUND - 4, 8):
		for wx in (x + 4, x + w / 2 + 1):
			if wx + 4 < x + w - 2:
				rect(wx, wy, 4, 3, "#D6ECFF", extra=' opacity=".9"')

# ---------------------------------------------------------------- gopuram (temple tower)
cx, lit, shade, ledge, niche = 128, "#F6B24C", "#E2902D", "#C9741C", "#A9581A"
# base wall
rect(cx - 34, 120, 34, GROUND - 120, lit)
rect(cx, 120, 34, GROUND - 120, shade)
rect(cx - 36, 118, 72, 3, ledge)
for px in (cx - 30, cx - 18, cx + 14, cx + 26):
	rect(px, 124, 4, 26, ledge, extra=' opacity=".45"')
a(f'<path d="M{cx-8} {GROUND}v-16a8 8 0 0 1 16 0v16z" fill="#8A4512"/>')
a(f'<path d="M{cx-5} {GROUND}v-14a5 5 0 0 1 10 0v14z" fill="#5E2E0B"/>')
# tiers
y, w = 118, 62
for i in range(6):
	th = 10 - i * 0.6
	top_w = w - 6
	poly([(cx - w / 2, y), (cx - top_w / 2, y - th), (cx, y - th), (cx, y)], lit)
	poly([(cx, y), (cx, y - th), (cx + top_w / 2, y - th), (cx + w / 2, y)], shade)
	rect(cx - top_w / 2 - 1.5, y - th - 2, top_w + 3, 2, ledge)
	# niches (little shrines) across each tier
	n = max(2, int(top_w // 10))
	step = top_w / n
	for k in range(n):
		nx = cx - top_w / 2 + step * k + step / 2 - 1.6
		arch_window(nx, y - th + 2.5, 3.2, th - 3.5, niche, ' opacity=".55"')
	y -= th + 2
	w = top_w
# barrel-vault crown (shala) with end horns and kalasam finials
sw = w + 2
a(f'<path d="M{f(cx-sw/2)} {f(y)}v-5a{f(sw/2)} 7 0 0 1 {f(sw)} 0v5z" fill="{lit}"/>')
a(f'<path d="M{f(cx)} {f(y)}v-12a{f(sw/2)} 7 0 0 1 {f(sw/2)} 7v5z" fill="{shade}"/>')
poly([(cx - sw / 2 - 3, y - 7), (cx - sw / 2 + 1, y - 4), (cx - sw / 2 + 1, y)], ledge)
poly([(cx + sw / 2 + 3, y - 7), (cx + sw / 2 - 1, y - 4), (cx + sw / 2 - 1, y)], ledge)
for k in range(5):
	kx = cx - 10 + k * 5
	ky = y - 12 + (abs(k - 2) * 1.6)
	rect(kx - 0.5, ky - 5, 1, 5, "#E0A11B")
	a(f'<circle cx="{f(kx)}" cy="{f(ky-6)}" r="1.6" fill="#FFCB45"/>')

# ---------------------------------------------------------------- Chennai Central station
cx, red, red_d, trim, win = 250, "#E2574A", "#C8433A", "#FBE7DA", "#FFF6EF"
# main wing
rect(196, 112, 108, GROUND - 112, red)
rect(196, 138, 108, 12, red_d)
rect(194, 110, 112, 3, trim)
for bx in range(196, 304, 6):
	rect(bx, 107, 3, 3, trim)
for row, wy in enumerate((117, 140)):
	for wx in list(range(214, 236, 7)) + list(range(266, 288, 7)):
		arch_window(wx, wy, 4, 8, win, ' opacity=".9"')
# corner turrets
for tx in (194, 292):
	rect(tx, 96, 14, GROUND - 96, red)
	rect(tx + 9, 96, 5, GROUND - 96, red_d)
	rect(tx - 1, 94, 16, 2.5, trim)
	a(f'<path d="M{tx} 94a7 7 0 0 1 14 0z" fill="{red_d}"/>')
	rect(tx + 6.5, 82, 1, 6, trim)
	for wy in (100, 118):
		arch_window(tx + 4.5, wy, 5, 9, win, ' opacity=".9"')
# clock tower
rect(cx - 13, 64, 26, GROUND - 64, red)
rect(cx, 64, 13, GROUND - 64, red_d)
rect(cx - 15, 62, 30, 3, trim)
rect(cx - 10, 50, 20, 12, red)
rect(cx, 50, 10, 12, red_d)
for ox in (cx - 7, cx - 1.5, cx + 4):
	arch_window(ox, 52, 3, 8, "#7A241E")
rect(cx - 12, 48, 24, 2.5, trim)
a(f'<path d="M{cx-11} 48Q{cx-10} 34 {cx} 28Q{cx+10} 34 {cx+11} 48z" fill="{red_d}"/>')
a(f'<path d="M{cx} 28Q{cx+10} 34 {cx+11} 48H{cx}z" fill="#A9352E"/>')
rect(cx - 0.6, 20, 1.2, 8, trim)
a(f'<circle cx="{cx}" cy="80" r="8" fill="{trim}"/><circle cx="{cx}" cy="80" r="6.4" fill="#fff"/>')
a(f'<path d="M{cx} 76.2V80l2.6 1.6" stroke="#4A1A16" stroke-width="1.2" fill="none" stroke-linecap="round"/>')
arch_window(cx - 6, 128, 12, 22, "#7A241E")
for wy in (96, 108):
	arch_window(cx - 6, wy, 4, 8, win, ' opacity=".9"')
	arch_window(cx + 2, wy, 4, 8, win, ' opacity=".9"')

# ---------------------------------------------------------------- glass towers
def tower(x, y, w, grad, crown=None):
	rect(x, y, w, GROUND - y, grad)
	rect(x + w * 0.66, y, w * 0.34, GROUND - y, "#000", extra=' opacity=".12"')
	for ly in range(int(y) + 5, GROUND, 5):
		rect(x, ly, w, 0.7, "#fff", extra=' opacity=".22"')
	for lx in (x + w / 3, x + 2 * w / 3):
		rect(lx, y, 0.7, GROUND - y, "#fff", extra=' opacity=".18"')
	# reflection streak
	poly([(x, y + 14), (x + w * 0.5, y), (x + w * 0.72, y), (x, y + 30)], "#fff", ' opacity=".18"')
	if crown == "spire":
		rect(x + w / 2 - 6, y - 4, 12, 4, grad)
		rect(x + w / 2 - 0.75, y - 18, 1.5, 14, "#0A4F96")
		a(f'<circle cx="{f(x + w/2)}" cy="{f(y-18)}" r="1.4" fill="#FF6B5E"/>')
	elif crown == "step":
		rect(x + 3, y - 5, w - 6, 5, grad)
		rect(x + 7, y - 9, w - 14, 4, grad)


tower(318, 74, 30, "url(#sl-g1)", "step")
tower(352, 94, 26, "url(#sl-g2)")
tower(382, 62, 26, "url(#sl-g3)", "spire")

# ---------------------------------------------------------------- palms
def palm(x, h, lean, s=1.0):
	top_x, top_y = x + lean, GROUND - h
	a(f'<path d="M{f(x-2.2*s)} {GROUND}Q{f(x+lean*0.3)} {f(GROUND-h*0.55)} {f(top_x-1*s)} {f(top_y)}h{f(2*s)}'
	  f'Q{f(x+lean*0.3+2.6*s)} {f(GROUND-h*0.55)} {f(x+2.2*s)} {GROUND}z" fill="#9A6A3C"/>')
	# ring marks sit on the trunk's centre line (same quadratic curve as the trunk outline)
	p1x, p1y = x + lean * 0.3 + 0.2 * s, GROUND - h * 0.55
	for k in range(1, 6):
		t = k / 6
		xx = (1 - t) ** 2 * x + 2 * (1 - t) * t * p1x + t * t * top_x
		yy = (1 - t) ** 2 * GROUND + 2 * (1 - t) * t * p1y + t * t * top_y
		a(f'<path d="M{f(xx-2*s)} {f(yy)}h{f(4*s)}" stroke="#7B5230" stroke-width=".8"/>')
	fronds = [(-26, 4, "#239A5E"), (-16, -6, "#2FB06B"), (-4, -12, "#2FB06B"), (10, -9, "#239A5E"),
	          (22, -2, "#2FB06B"), (26, 7, "#1F8752"), (-22, 10, "#1F8752")]
	for dx, dy, col in fronds:
		ex, ey = top_x + dx * s, top_y + dy * s + 6 * s
		mx, my = top_x + dx * s * 0.5, top_y + dy * s - 6 * s
		a(f'<path d="M{f(top_x)} {f(top_y)}Q{f(mx)} {f(my-3*s)} {f(ex)} {f(ey)}Q{f(mx)} {f(my+3*s)} {f(top_x)} {f(top_y)}z" fill="{col}"/>')
	for cxo in (-2, 1.5):
		a(f'<circle cx="{f(top_x + cxo*s)}" cy="{f(top_y + 3*s)}" r="{f(1.8*s)}" fill="#6B4A22"/>')


palm(62, 50, 8, 1.0)
palm(176, 38, -6, 0.8)
palm(424, 52, -9, 1.05)
palm(446, 34, 5, 0.75)

# ---------------------------------------------------------------- Marina: sand + sea
a(f'<path d="M0 {GROUND}H{W}V160H0z" fill="#FBE3B6"/>')
a(f'<path d="M0 {GROUND}H{W}v2H0z" fill="#F2CF92"/>')
a('<path d="M0 158q60-4 120 0t120 0 120 0 120 0V180H0z" fill="url(#sl-sea)"/>')
a('<path d="M0 164q20-3 40 0t40 0 40 0 40 0 40 0 40 0 40 0 40 0 40 0 40 0 40 0 40 0" stroke="#BFE3FF" stroke-width="1.4" fill="none" opacity=".8"/>')
a('<path d="M-20 172q20-3 40 0t40 0 40 0 40 0 40 0 40 0 40 0 40 0 40 0 40 0 40 0 40 0 40 0" stroke="#8ECDFF" stroke-width="1.4" fill="none" opacity=".7"/>')

body = "\n".join("\t\t" + line for line in "\n".join(out).splitlines())
TARGET.write_text(f"""<!-- Generated by scripts/make_skyline.py - edit that script, not this file. Ids are prefixed "sl-" to avoid clashes. -->
<template>
	<svg viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMax slice" class="block h-full w-full" role="img" aria-label="Chennai city skyline">
{body}
	</svg>
</template>
""")
print("wrote", TARGET)
