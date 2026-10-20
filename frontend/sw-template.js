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

const CACHE_VERSION = "__CACHE_VERSION__"
const PRECACHE = __PRECACHE__
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
