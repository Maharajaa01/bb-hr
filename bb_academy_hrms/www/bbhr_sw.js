/**
 * BB HR service worker.
 *
 * Source of truth: frontend/sw-template.js. Built into bb_academy_hrms/www/bbhr_sw.js
 * by frontend/scripts/make-page.mjs, which stamps CACHE_VERSION and the PRECACHE
 * list on every build - never edit www/bbhr_sw.js by hand.
 *
 * Rules, most important first:
 *   1. HR data is never cached. /api/, /private/, /files/ and anything that is not
 *      a static build asset goes straight to the network, untouched. Salary slips,
 *      attendance and check-in calls therefore cannot be served stale or offline.
 *   2. Pages under /bbhr/ are network-only. Offline, a small built-in notice is
 *      shown instead of a cached page (the rendered page carries a session token).
 *   3. Hashed build assets are precached and served cache-first - their names
 *      change whenever their content does.
 *   4. A new worker waits until the page asks it to take over (Update banner),
 *      so a half-finished check-in is never interrupted by a reload.
 */

const CACHE_VERSION = "1792468167035"
const PRECACHE = [
	"/assets/bb_academy_hrms/bbhr/assets/AppBar.vue_vue_type_script_setup_true_lang.9r4ypaQc.js",
	"/assets/bb_academy_hrms/bbhr/assets/AppButton.vue_vue_type_script_setup_true_lang.xK-veB-U.js",
	"/assets/bb_academy_hrms/bbhr/assets/AppShell.BcD4p23W.js",
	"/assets/bb_academy_hrms/bbhr/assets/AttendanceHistory.CvnBW2wP.js",
	"/assets/bb_academy_hrms/bbhr/assets/Avatar.vue_vue_type_script_setup_true_lang.BCUbAvVx.js",
	"/assets/bb_academy_hrms/bbhr/assets/CheckIn.x7vDj4TW.js",
	"/assets/bb_academy_hrms/bbhr/assets/Dashboard.CDtCN2a4.js",
	"/assets/bb_academy_hrms/bbhr/assets/Directory.rP7Z97cK.js",
	"/assets/bb_academy_hrms/bbhr/assets/EmptyState.vue_vue_type_script_setup_true_lang.9dmQMiGr.js",
	"/assets/bb_academy_hrms/bbhr/assets/Exceptions.cP8rdM5t.js",
	"/assets/bb_academy_hrms/bbhr/assets/Forbidden.B--8E-tP.js",
	"/assets/bb_academy_hrms/bbhr/assets/Holidays.CBhLpZvQ.js",
	"/assets/bb_academy_hrms/bbhr/assets/HrDashboard.Da_y_em5.js",
	"/assets/bb_academy_hrms/bbhr/assets/IconButton.vue_vue_type_script_setup_true_lang.Dm7ZjrhP.js",
	"/assets/bb_academy_hrms/bbhr/assets/LogTable.vue_vue_type_script_setup_true_lang.C8mVGC9d.js",
	"/assets/bb_academy_hrms/bbhr/assets/Login.C2QJ2SQT.js",
	"/assets/bb_academy_hrms/bbhr/assets/MaskedAmount.vue_vue_type_script_setup_true_lang.C99HY6qa.js",
	"/assets/bb_academy_hrms/bbhr/assets/NoEmployee.C464QzsF.js",
	"/assets/bb_academy_hrms/bbhr/assets/NotFound.dl9CGRG6.js",
	"/assets/bb_academy_hrms/bbhr/assets/Pagination.vue_vue_type_script_setup_true_lang.wSt-8GKU.js",
	"/assets/bb_academy_hrms/bbhr/assets/Profile.D3hYNZWh.js",
	"/assets/bb_academy_hrms/bbhr/assets/SalarySlipDetail.C_ocEdD4.js",
	"/assets/bb_academy_hrms/bbhr/assets/SalarySlips.9omuPWGU.js",
	"/assets/bb_academy_hrms/bbhr/assets/Spot.vue_vue_type_script_setup_true_lang.Cuh4xk0J.js",
	"/assets/bb_academy_hrms/bbhr/assets/StatCard.vue_vue_type_script_setup_true_lang.DhQopthW.js",
	"/assets/bb_academy_hrms/bbhr/assets/StatTile.vue_vue_type_script_setup_true_lang.BTXsBLP_.js",
	"/assets/bb_academy_hrms/bbhr/assets/StatusBadge.vue_vue_type_script_setup_true_lang.CdiGj4Np.js",
	"/assets/bb_academy_hrms/bbhr/assets/Team.B6p_ZuAP.js",
	"/assets/bb_academy_hrms/bbhr/assets/calendar-days.BFchCZ5V.js",
	"/assets/bb_academy_hrms/bbhr/assets/calendar-x.2GYcee-C.js",
	"/assets/bb_academy_hrms/bbhr/assets/chevron-left.hrH3JzEX.js",
	"/assets/bb_academy_hrms/bbhr/assets/chevron-right.DmhElFEP.js",
	"/assets/bb_academy_hrms/bbhr/assets/download.BHdOpTGY.js",
	"/assets/bb_academy_hrms/bbhr/assets/eye.BfQB5vXC.js",
	"/assets/bb_academy_hrms/bbhr/assets/format.CKqIGVBr.js",
	"/assets/bb_academy_hrms/bbhr/assets/index.8ZtndINK.js",
	"/assets/bb_academy_hrms/bbhr/assets/index.Ba-G_K02.js",
	"/assets/bb_academy_hrms/bbhr/assets/index.C4YXhHmg.js",
	"/assets/bb_academy_hrms/bbhr/assets/index.DrSP3RVE.css",
	"/assets/bb_academy_hrms/bbhr/assets/indian-rupee.Cuw-XzWc.js",
	"/assets/bb_academy_hrms/bbhr/assets/lock.Dyu_1w0c.js",
	"/assets/bb_academy_hrms/bbhr/assets/log-out.IRm3R4bP.js",
	"/assets/bb_academy_hrms/bbhr/assets/mail.CJAmWxD4.js",
	"/assets/bb_academy_hrms/bbhr/assets/map-pin.DBm7d3c_.js",
	"/assets/bb_academy_hrms/bbhr/assets/plane.CbnZNZbm.js",
	"/assets/bb_academy_hrms/bbhr/assets/refresh-cw._pPYFhTB.js",
	"/assets/bb_academy_hrms/bbhr/assets/search.B0sX0BZl.js",
	"/assets/bb_academy_hrms/bbhr/assets/timer.FVh3XqU4.js",
	"/assets/bb_academy_hrms/bbhr/assets/ui.r2exqjs1.js",
	"/assets/bb_academy_hrms/bbhr/assets/useNav.DdzK1Amf.js",
	"/assets/bb_academy_hrms/bbhr/assets/useResource.DiIwlaFs.js",
	"/assets/bb_academy_hrms/bbhr/assets/user-x.yHDNmWfF.js",
	"/assets/bb_academy_hrms/bbhr/assets/users.H0Iv4KT9.js",
	"/assets/bb_academy_hrms/bbhr/icons/apple-touch-icon.png",
	"/assets/bb_academy_hrms/bbhr/icons/icon-192.png",
	"/assets/bb_academy_hrms/bbhr/icons/icon-512.png",
	"/assets/bb_academy_hrms/bbhr/icons/maskable-512.png",
	"/assets/bb_academy_hrms/bbhr/illustrations/README.md",
	"/assets/bb_academy_hrms/bbhr/illustrations/alert.svg",
	"/assets/bb_academy_hrms/bbhr/illustrations/attendance.svg",
	"/assets/bb_academy_hrms/bbhr/illustrations/chart.svg",
	"/assets/bb_academy_hrms/bbhr/illustrations/checkin.svg",
	"/assets/bb_academy_hrms/bbhr/illustrations/directory.svg",
	"/assets/bb_academy_hrms/bbhr/illustrations/empty.svg",
	"/assets/bb_academy_hrms/bbhr/illustrations/holiday.svg",
	"/assets/bb_academy_hrms/bbhr/illustrations/leave.svg",
	"/assets/bb_academy_hrms/bbhr/illustrations/login.svg",
	"/assets/bb_academy_hrms/bbhr/illustrations/profile.svg",
	"/assets/bb_academy_hrms/bbhr/illustrations/salary.svg",
	"/assets/bb_academy_hrms/bbhr/illustrations/team.svg",
	"/assets/bb_academy_hrms/bbhr/manifest.json"
]
const CACHE = `bbhr-static-${CACHE_VERSION}`
const ASSET_PATH = "/assets/bb_academy_hrms/bbhr/"
const APP_SCOPE = "/bbhr"

const OFFLINE_HTML = `<!doctype html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#048EFF"><title>Offline · BB HR</title>
<style>
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#FFFFFF;color:#212121;font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.c{max-width:22rem;padding:2rem;text-align:center}.b{width:3.5rem;height:3.5rem;border-radius:1rem;background:#048EFF;color:#fff;display:grid;place-items:center;margin:0 auto 1.25rem;font-weight:900}
h1{font-size:1.25rem;margin:0 0 .5rem}p{color:#808080;margin:0 0 1.5rem}
button{min-height:3rem;padding:0 1.5rem;border:0;border-radius:.75rem;background:#048EFF;color:#fff;font:inherit;font-weight:700;cursor:pointer}
</style></head><body><main class="c"><div class="b">BB</div><h1>You're offline</h1>
<p>BB HR needs a connection to check you in and show your attendance and payslips. Nothing is recorded while offline.</p>
<button onclick="location.reload()">Try again</button></main></body></html>`

self.addEventListener("install", (event) => {
	event.waitUntil(
		caches
			.open(CACHE)
			.then((cache) => cache.addAll(PRECACHE))
			.catch(() => undefined),
	)
})

self.addEventListener("activate", (event) => {
	event.waitUntil(
		caches
			.keys()
			.then((keys) => Promise.all(keys.filter((k) => k.startsWith("bbhr-") && k !== CACHE).map((k) => caches.delete(k))))
			.then(() => self.clients.claim()),
	)
})

self.addEventListener("message", (event) => {
	if (event.data && event.data.type === "SKIP_WAITING") self.skipWaiting()
})

self.addEventListener("fetch", (event) => {
	const req = event.request
	if (req.method !== "GET") return
	const url = new URL(req.url)
	if (url.origin !== self.location.origin) return

	// pages: network only, offline notice as fallback - never cached
	if (req.mode === "navigate" && (url.pathname === APP_SCOPE || url.pathname.startsWith(APP_SCOPE + "/"))) {
		event.respondWith(
			fetch(req).catch(
				() => new Response(OFFLINE_HTML, { status: 503, headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" } }),
			),
		)
		return
	}

	// only our own static build output is ever cached
	if (!url.pathname.startsWith(ASSET_PATH) || url.search) return

	event.respondWith(
		caches.open(CACHE).then(async (cache) => {
			const hit = await cache.match(req)
			const hashed = url.pathname.startsWith(ASSET_PATH + "assets/")
			if (hit && hashed) return hit
			const network = fetch(req)
				.then((res) => {
					if (res.ok && res.type === "basic") cache.put(req, res.clone())
					return res
				})
				.catch(() => hit || Response.error())
			return hit || network
		}),
	)
})
