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

const CACHE_VERSION = "1793638953690"
const PRECACHE = [
	"/assets/bb_academy_hrms/bbhr/assets/AppBar.vue_vue_type_script_setup_true_lang.CN3dbxpz.js",
	"/assets/bb_academy_hrms/bbhr/assets/AppButton.vue_vue_type_script_setup_true_lang.CacXhPgM.js",
	"/assets/bb_academy_hrms/bbhr/assets/AppShell.CKGc23dZ.js",
	"/assets/bb_academy_hrms/bbhr/assets/AttendanceHistory.D_BjDYbr.js",
	"/assets/bb_academy_hrms/bbhr/assets/Avatar.vue_vue_type_script_setup_true_lang.Ln1BHgPp.js",
	"/assets/bb_academy_hrms/bbhr/assets/BrandLogo.Dh1yAWWt.js",
	"/assets/bb_academy_hrms/bbhr/assets/CheckIn.CExnS-Sq.js",
	"/assets/bb_academy_hrms/bbhr/assets/Dashboard.DBdBdfot.js",
	"/assets/bb_academy_hrms/bbhr/assets/Directory.BQl52cEL.js",
	"/assets/bb_academy_hrms/bbhr/assets/EmptyState.vue_vue_type_script_setup_true_lang.D616fOWb.js",
	"/assets/bb_academy_hrms/bbhr/assets/Exceptions.B6FXHfXp.js",
	"/assets/bb_academy_hrms/bbhr/assets/Forbidden.a61mprTN.js",
	"/assets/bb_academy_hrms/bbhr/assets/Holidays.DfAPEyNv.js",
	"/assets/bb_academy_hrms/bbhr/assets/HrDashboard.zSD1U5Q8.js",
	"/assets/bb_academy_hrms/bbhr/assets/IconButton.vue_vue_type_script_setup_true_lang.DXJrM3cN.js",
	"/assets/bb_academy_hrms/bbhr/assets/LogTable.vue_vue_type_script_setup_true_lang.BNY8W9iq.js",
	"/assets/bb_academy_hrms/bbhr/assets/Login.CJf_ExUQ.js",
	"/assets/bb_academy_hrms/bbhr/assets/MaskedAmount.vue_vue_type_script_setup_true_lang.C9VoHbCR.js",
	"/assets/bb_academy_hrms/bbhr/assets/NoEmployee.DJADJAqy.js",
	"/assets/bb_academy_hrms/bbhr/assets/NotFound.C1FKqG3y.js",
	"/assets/bb_academy_hrms/bbhr/assets/Pagination.vue_vue_type_script_setup_true_lang.z7woDgt6.js",
	"/assets/bb_academy_hrms/bbhr/assets/Profile.9FmbERbm.js",
	"/assets/bb_academy_hrms/bbhr/assets/SalarySlipDetail.9hl6Bj3t.js",
	"/assets/bb_academy_hrms/bbhr/assets/SalarySlips.Dh_rOeg8.js",
	"/assets/bb_academy_hrms/bbhr/assets/Segmented.vue_vue_type_script_setup_true_lang.ByyFg-7S.js",
	"/assets/bb_academy_hrms/bbhr/assets/ShiftPlanner.BQdSmVfU.js",
	"/assets/bb_academy_hrms/bbhr/assets/ShiftPlanner.fokrU9I6.css",
	"/assets/bb_academy_hrms/bbhr/assets/Spot.vue_vue_type_script_setup_true_lang.Bar-YjrD.js",
	"/assets/bb_academy_hrms/bbhr/assets/StatCard.vue_vue_type_script_setup_true_lang.BZumPxUb.js",
	"/assets/bb_academy_hrms/bbhr/assets/StatTile.vue_vue_type_script_setup_true_lang.C7E1i2kq.js",
	"/assets/bb_academy_hrms/bbhr/assets/StatusBadge.vue_vue_type_script_setup_true_lang.BU3KqZxM.js",
	"/assets/bb_academy_hrms/bbhr/assets/Team.BkjPhc5X.js",
	"/assets/bb_academy_hrms/bbhr/assets/_plugin-vue_export-helper.DlAUqK2U.js",
	"/assets/bb_academy_hrms/bbhr/assets/alert.BX67RVA3.svg",
	"/assets/bb_academy_hrms/bbhr/assets/attendance.Dwzusxty.svg",
	"/assets/bb_academy_hrms/bbhr/assets/calendar-clock.CxKvCev1.js",
	"/assets/bb_academy_hrms/bbhr/assets/calendar-days.C-8AzPSv.js",
	"/assets/bb_academy_hrms/bbhr/assets/calendar-x.Cm2zlyeU.js",
	"/assets/bb_academy_hrms/bbhr/assets/chart.45I4LjWF.svg",
	"/assets/bb_academy_hrms/bbhr/assets/checkin.D1E1Pr0e.svg",
	"/assets/bb_academy_hrms/bbhr/assets/chevron-left.B0sOrYs6.js",
	"/assets/bb_academy_hrms/bbhr/assets/chevron-right.CwZIWjxy.js",
	"/assets/bb_academy_hrms/bbhr/assets/clock.CawIzQFv.js",
	"/assets/bb_academy_hrms/bbhr/assets/directory.aUNXHluA.svg",
	"/assets/bb_academy_hrms/bbhr/assets/download.DFVRRzPI.js",
	"/assets/bb_academy_hrms/bbhr/assets/empty.yir5vKpY.svg",
	"/assets/bb_academy_hrms/bbhr/assets/eye.DFLQjLUL.js",
	"/assets/bb_academy_hrms/bbhr/assets/format.BfFRiTt7.js",
	"/assets/bb_academy_hrms/bbhr/assets/holiday.CAZTqgDC.svg",
	"/assets/bb_academy_hrms/bbhr/assets/index.BP9wCfH6.css",
	"/assets/bb_academy_hrms/bbhr/assets/index.BgSBV1ct.js",
	"/assets/bb_academy_hrms/bbhr/assets/index.CC-XD46L.js",
	"/assets/bb_academy_hrms/bbhr/assets/index.pl5I_yFK.js",
	"/assets/bb_academy_hrms/bbhr/assets/indian-rupee.DqPPiJIf.js",
	"/assets/bb_academy_hrms/bbhr/assets/leave.CKsyJaG9.svg",
	"/assets/bb_academy_hrms/bbhr/assets/lock.Cht3ksgl.js",
	"/assets/bb_academy_hrms/bbhr/assets/log-out.CuwItRdG.js",
	"/assets/bb_academy_hrms/bbhr/assets/login.CAztghva.svg",
	"/assets/bb_academy_hrms/bbhr/assets/mail.BFy4Ay4W.js",
	"/assets/bb_academy_hrms/bbhr/assets/map-pin.SIfcMkLq.js",
	"/assets/bb_academy_hrms/bbhr/assets/plane.DNANc51N.js",
	"/assets/bb_academy_hrms/bbhr/assets/plus.DNdtMXF3.js",
	"/assets/bb_academy_hrms/bbhr/assets/profile.CTq6XAb9.svg",
	"/assets/bb_academy_hrms/bbhr/assets/refresh-cw.B9v_w8qh.js",
	"/assets/bb_academy_hrms/bbhr/assets/salary.BK9gbSfJ.svg",
	"/assets/bb_academy_hrms/bbhr/assets/search.Ck6mZw-3.js",
	"/assets/bb_academy_hrms/bbhr/assets/shield-check.7WONyiqq.js",
	"/assets/bb_academy_hrms/bbhr/assets/team.wagy_Pt5.svg",
	"/assets/bb_academy_hrms/bbhr/assets/ui.M7xJMtkG.js",
	"/assets/bb_academy_hrms/bbhr/assets/useNav.dibFNOG9.js",
	"/assets/bb_academy_hrms/bbhr/assets/useResource.DuH0Scy8.js",
	"/assets/bb_academy_hrms/bbhr/assets/user-check.Cm5ELJbT.js",
	"/assets/bb_academy_hrms/bbhr/assets/user-x.CflAbiN7.js",
	"/assets/bb_academy_hrms/bbhr/assets/users.C2JS8s5f.js",
	"/assets/bb_academy_hrms/bbhr/icons/apple-touch-icon.png",
	"/assets/bb_academy_hrms/bbhr/icons/favicon-32.png",
	"/assets/bb_academy_hrms/bbhr/icons/icon-192.png",
	"/assets/bb_academy_hrms/bbhr/icons/icon-512.png",
	"/assets/bb_academy_hrms/bbhr/icons/maskable-512.png",
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
