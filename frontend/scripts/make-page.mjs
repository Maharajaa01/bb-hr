/**
 * Turn the Vite build into a Frappe website page + root-scoped service worker.
 *
 * Run after `vite build`:
 *   - www/bbhr.html  : built index.html with this session's CSRF token injected (Frappe renders it as Jinja)
 *   - www/bbhr_sw.js : sw-template.js stamped with a fresh CACHE_VERSION and the list of built assets
 */
import { mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs"
import { dirname, join, relative, resolve } from "node:path"
import { fileURLToPath } from "node:url"

const HERE = dirname(fileURLToPath(import.meta.url))
const FRONTEND = resolve(HERE, "..")
const APP = resolve(FRONTEND, "../bb_academy_hrms")
const OUT = resolve(APP, "public/bbhr")
const BASE = "/assets/bb_academy_hrms/bbhr/"

function write(target, contents) {
	mkdirSync(dirname(target), { recursive: true })
	writeFileSync(target, contents)
	console.log(`make-page: wrote ${relative(resolve(APP, ".."), target)}`)
}

// ---------------------------------------------------------------- SPA shell
const html = readFileSync(join(OUT, "index.html"), "utf-8")
if (!html.includes("</head>")) {
	console.error("make-page: built index.html has no </head>")
	process.exit(1)
}
const page = html.replace(
	"</head>",
	'    <script>window.csrf_token = "{{ csrf_token }}";</script>\n  </head>',
)
write(resolve(APP, "www/bbhr.html"), page)

// ---------------------------------------------------------- service worker
function walk(dir) {
	return readdirSync(dir).flatMap((name) => {
		const p = join(dir, name)
		return statSync(p).isDirectory() ? walk(p) : [p]
	})
}
const precache = walk(OUT)
	.map((p) => relative(OUT, p).split("\\").join("/"))
	.filter((p) => p !== "index.html" && !p.startsWith(".vite/"))
	.map((p) => BASE + p)
	.sort()

const sw = readFileSync(resolve(FRONTEND, "sw-template.js"), "utf-8")
	.replace("__CACHE_VERSION__", String(Date.now()))
	.replace("__PRECACHE__", JSON.stringify(precache, null, "\t"))
write(resolve(APP, "www/bbhr_sw.js"), sw)
console.log(`make-page: ${precache.length} files precached`)
