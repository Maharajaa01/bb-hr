/** Formatting helpers. Server datetimes are naive site-local (Asia/Kolkata) strings: "2026-10-16 09:05:00". */

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
export const MONTH_NAMES = [
	"January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December",
]
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

/** Parse "YYYY-MM-DD[ HH:MM[:SS[.ffffff]]]" without timezone shifts. */
export function parseLocal(value: string | null | undefined): Date | null {
	if (!value) return null
	const m = /^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?/.exec(value)
	if (!m) return null
	return new Date(+m[1], +m[2] - 1, +m[3], +(m[4] ?? 0), +(m[5] ?? 0), +(m[6] ?? 0))
}

export function isoDate(d: Date): string {
	const pad = (n: number) => String(n).padStart(2, "0")
	return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function formatTime(value: string | null | undefined): string {
	const d = parseLocal(value)
	if (!d) return "—"
	let h = d.getHours()
	const ampm = h >= 12 ? "PM" : "AM"
	h = h % 12 || 12
	return `${h}:${String(d.getMinutes()).padStart(2, "0")} ${ampm}`
}

export function formatDate(value: string | null | undefined, opts: { weekday?: boolean; year?: boolean } = {}): string {
	const d = parseLocal(value)
	if (!d) return "—"
	let out = `${d.getDate()} ${MONTHS[d.getMonth()]}`
	if (opts.year !== false) out += ` ${d.getFullYear()}`
	if (opts.weekday) out = `${DAYS[d.getDay()]}, ${out}`
	return out
}

export function weekday(value: string): string {
	const d = parseLocal(value)
	return d ? DAYS[d.getDay()] : ""
}

export function monthLabel(value: string): string {
	const d = parseLocal(value)
	return d ? `${MONTH_NAMES[d.getMonth()]} ${d.getFullYear()}` : ""
}

export function formatHours(hours: number | null | undefined): string {
	if (hours === null || hours === undefined || Number.isNaN(hours)) return "—"
	const total = Math.round(hours * 60)
	const h = Math.floor(total / 60)
	const m = total % 60
	if (!h) return `${m}m`
	return m ? `${h}h ${m}m` : `${h}h`
}

const currencyFormatters: Record<string, Intl.NumberFormat> = {}

export function formatMoney(amount: number | null | undefined, currency = "INR"): string {
	if (amount === null || amount === undefined) return "—"
	if (!currencyFormatters[currency]) {
		currencyFormatters[currency] = new Intl.NumberFormat("en-IN", {
			style: "currency",
			currency,
			maximumFractionDigits: 2,
			minimumFractionDigits: 0,
		})
	}
	return currencyFormatters[currency].format(amount)
}

export function formatDistance(metres: number | null | undefined): string {
	if (metres === null || metres === undefined) return "—"
	if (metres < 1000) return `${Math.round(metres)} m`
	return `${(metres / 1000).toFixed(metres < 10000 ? 1 : 0)} km`
}

export function greeting(now = new Date()): string {
	const h = now.getHours()
	if (h < 12) return "Good morning"
	if (h < 17) return "Good afternoon"
	return "Good evening"
}

export function initials(name: string | null | undefined): string {
	if (!name || !name.trim()) return "?"
	const words = name.trim().split(/\s+/)
	// names here often lead with an initial ("S PREETHI"); prefer the real words
	const long = words.filter((w) => w.length > 1)
	const pick = long.length ? long : words
	return (pick.length > 1 ? pick[0][0] + pick[pick.length - 1][0] : pick[0].slice(0, 2)).toUpperCase()
}

export function titleCase(s: string | null | undefined): string {
	if (!s) return ""
	return s
		.toLowerCase()
		.replace(/\s+/g, " ")
		.trim()
		.replace(/(^|[\s(.])([a-z])/g, (_m, p, c) => p + c.toUpperCase())
}

/** "16th Oct, 2026" */
export function ordinalDate(value: string | Date): string {
	const d = typeof value === "string" ? parseLocal(value) : value
	if (!d) return ""
	const n = d.getDate()
	const suffix = n % 10 === 1 && n !== 11 ? "st" : n % 10 === 2 && n !== 12 ? "nd" : n % 10 === 3 && n !== 13 ? "rd" : "th"
	return `${n}${suffix} ${MONTHS[d.getMonth()]}, ${d.getFullYear()}`
}

/** "06 : 27 : 42" */
export function clock(seconds: number): string {
	const s = Math.max(0, Math.floor(seconds))
	const pad = (x: number) => String(x).padStart(2, "0")
	return `${pad(Math.floor(s / 3600))} : ${pad(Math.floor((s % 3600) / 60))} : ${pad(s % 60)}`
}
