/**
 * BB HRMS service worker.
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

const CACHE_VERSION = "1792470453934"
const PRECACHE = [
	"/assets/bb_academy_hrms/bbhr/assets/AppBar.vue_vue_type_script_setup_true_lang.BeIQUXp8.js",
	"/assets/bb_academy_hrms/bbhr/assets/AppButton.vue_vue_type_script_setup_true_lang.B0XNiVMR.js",
	"/assets/bb_academy_hrms/bbhr/assets/AppShell.Dh_YeUvQ.js",
	"/assets/bb_academy_hrms/bbhr/assets/AttendanceHistory.Cdz4VpHr.js",
	"/assets/bb_academy_hrms/bbhr/assets/Avatar.vue_vue_type_script_setup_true_lang.CUr59fxz.js",
	"/assets/bb_academy_hrms/bbhr/assets/CheckIn.BArjqkFY.js",
	"/assets/bb_academy_hrms/bbhr/assets/Dashboard.LV0Uzb7U.js",
	"/assets/bb_academy_hrms/bbhr/assets/Directory.C8TK-9Gk.js",
	"/assets/bb_academy_hrms/bbhr/assets/EmptyState.vue_vue_type_script_setup_true_lang.BH2w17kb.js",
	"/assets/bb_academy_hrms/bbhr/assets/Exceptions.Cvd3uXg9.js",
	"/assets/bb_academy_hrms/bbhr/assets/Forbidden.C1x8aolI.js",
	"/assets/bb_academy_hrms/bbhr/assets/Holidays.CFCMdFII.js",
	"/assets/bb_academy_hrms/bbhr/assets/HrDashboard.B4KRKSqZ.js",
	"/assets/bb_academy_hrms/bbhr/assets/IconButton.vue_vue_type_script_setup_true_lang.CLF4sutf.js",
	"/assets/bb_academy_hrms/bbhr/assets/LogTable.vue_vue_type_script_setup_true_lang.BAjTeOFX.js",
	"/assets/bb_academy_hrms/bbhr/assets/Login.DBI0kj0k.js",
	"/assets/bb_academy_hrms/bbhr/assets/MaskedAmount.vue_vue_type_script_setup_true_lang.OXfMaqN_.js",
	"/assets/bb_academy_hrms/bbhr/assets/NoEmployee.D9Gpsgrh.js",
	"/assets/bb_academy_hrms/bbhr/assets/NotFound.BPtng40f.js",
	"/assets/bb_academy_hrms/bbhr/assets/Pagination.vue_vue_type_script_setup_true_lang.C59CZXMc.js",
	"/assets/bb_academy_hrms/bbhr/assets/Profile.CTpGSUGu.js",
	"/assets/bb_academy_hrms/bbhr/assets/SalarySlipDetail.DDr5c25H.js",
	"/assets/bb_academy_hrms/bbhr/assets/SalarySlips.RTs7KQ6U.js",
	"/assets/bb_academy_hrms/bbhr/assets/Spot.vue_vue_type_script_setup_true_lang.DKv4jkgr.js",
	"/assets/bb_academy_hrms/bbhr/assets/StatCard.vue_vue_type_script_setup_true_lang.Ctj_QpCT.js",
	"/assets/bb_academy_hrms/bbhr/assets/StatTile.vue_vue_type_script_setup_true_lang.CbHy989f.js",
	"/assets/bb_academy_hrms/bbhr/assets/StatusBadge.vue_vue_type_script_setup_true_lang.BJkwTyLe.js",
	"/assets/bb_academy_hrms/bbhr/assets/Team.DtqyWm-N.js",
	"/assets/bb_academy_hrms/bbhr/assets/calendar-days.C6l0AH1M.js",
	"/assets/bb_academy_hrms/bbhr/assets/calendar-x.12m0IYj8.js",
	"/assets/bb_academy_hrms/bbhr/assets/chevron-left.V9T6HVJy.js",
	"/assets/bb_academy_hrms/bbhr/assets/chevron-right.SDScsMj6.js",
	"/assets/bb_academy_hrms/bbhr/assets/download.Cj-lG-DX.js",
	"/assets/bb_academy_hrms/bbhr/assets/eye.o8uHKSD-.js",
	"/assets/bb_academy_hrms/bbhr/assets/format.Bmwu8fos.js",
	"/assets/bb_academy_hrms/bbhr/assets/index.BL2JDBF6.js",
	"/assets/bb_academy_hrms/bbhr/assets/index.DRtNTA1M.js",
	"/assets/bb_academy_hrms/bbhr/assets/index.DrSP3RVE.css",
	"/assets/bb_academy_hrms/bbhr/assets/index.DzPSi2eQ.js",
	"/assets/bb_academy_hrms/bbhr/assets/indian-rupee.z3Jr7z-A.js",
	"/assets/bb_academy_hrms/bbhr/assets/lock.CF49nwAr.js",
	"/assets/bb_academy_hrms/bbhr/assets/log-out.D8qRmjeM.js",
	"/assets/bb_academy_hrms/bbhr/assets/mail.g-RKpSiG.js",
	"/assets/bb_academy_hrms/bbhr/assets/map-pin.yF1oj9nr.js",
	"/assets/bb_academy_hrms/bbhr/assets/plane.BtaWN-7V.js",
	"/assets/bb_academy_hrms/bbhr/assets/refresh-cw.D4Vqrcd4.js",
	"/assets/bb_academy_hrms/bbhr/assets/search.D85UzYjt.js",
	"/assets/bb_academy_hrms/bbhr/assets/timer.Dz3cI8wC.js",
	"/assets/bb_academy_hrms/bbhr/assets/ui.C-hMwAO_.js",
	"/assets/bb_academy_hrms/bbhr/assets/useNav.CR_ny7u8.js",
	"/assets/bb_academy_hrms/bbhr/assets/useResource.BmSNZ_WM.js",
	"/assets/bb_academy_hrms/bbhr/assets/user-x.6uNIaGHO.js",
	"/assets/bb_academy_hrms/bbhr/assets/users.0APwt__x.js",
	"/assets/bb_academy_hrms/bbhr/icons/apple-touch-icon.png",
	"/assets/bb_academy_hrms/bbhr/icons/favicon-32.png",
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
<meta name="theme-color" content="#048EFF"><title>Offline · BB HRMS</title>
<style>
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#FFFFFF;color:#212121;font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.c{max-width:22rem;padding:2rem;text-align:center}.b{width:3.5rem;height:3.5rem;border-radius:1rem;background:#048EFF;color:#fff;display:grid;place-items:center;margin:0 auto 1.25rem;font-weight:900}
h1{font-size:1.25rem;margin:0 0 .5rem}p{color:#808080;margin:0 0 1.5rem}
button{min-height:3rem;padding:0 1.5rem;border:0;border-radius:.75rem;background:#048EFF;color:#fff;font:inherit;font-weight:700;cursor:pointer}
</style></head><body><main class="c"><div class="b">BB</div><h1>You're offline</h1>
<p>BB HRMS needs a connection to check you in and show your attendance and payslips. Nothing is recorded while offline.</p>
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
