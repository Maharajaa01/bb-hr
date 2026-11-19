/** Shift timing helpers; the overlap rules mirror api/shifts.py. Times are "HH:MM" (24 h). */
import { Moon, Sun, Sunrise, Sunset, type LucideIcon } from "lucide-vue-next"

export const DAY = 24 * 60

export function toMinutes(t: string): number {
	const m = /^(\d{1,2}):(\d{2})/.exec(t || "")
	return m ? (+m[1] * 60 + +m[2]) % DAY : NaN
}

/** [start, end) with end > start; an overnight shift ends after 1440. */
export function span(start: string, end: string): [number, number] {
	const s = toMinutes(start)
	let e = toMinutes(end)
	if (e <= s) e += DAY
	return [s, e]
}

export function timesOverlap(a: { start: string; end: string }, b: { start: string; end: string }): boolean {
	const [as, ae] = span(a.start, a.end)
	const [bs, be] = span(b.start, b.end)
	return [-DAY, 0, DAY].some((d) => as < be + d && bs + d < ae)
}

/** Inclusive date ranges; null end = open-ended. ISO strings compare correctly. */
export function datesOverlap(aFrom: string, aTo: string | null, bFrom: string, bTo: string | null): boolean {
	return (!aTo || aTo >= bFrom) && (!bTo || bTo >= aFrom)
}

export function isOvernight(start: string, end: string): boolean {
	return toMinutes(end) <= toMinutes(start)
}

/** "6:15 AM" */
export function time12(t: string): string {
	const mins = toMinutes(t)
	if (Number.isNaN(mins)) return "—"
	const h = Math.floor(mins / 60)
	return `${h % 12 || 12}:${String(mins % 60).padStart(2, "0")} ${h >= 12 ? "PM" : "AM"}`
}

export function timeRange(start: string, end: string): string {
	return `${time12(start)} – ${time12(end)}`
}

/** "1 h 30 m" */
export function duration(start: string, end: string): string {
	const [s, e] = span(start, end)
	const mins = e - s
	const h = Math.floor(mins / 60)
	const m = mins % 60
	return [h ? `${h} h` : "", m ? `${m} m` : ""].filter(Boolean).join(" ") || "0 m"
}

export interface Period {
	key: "morning" | "midday" | "evening" | "night"
	label: string
	icon: LucideIcon
	/** chip background / text / border */
	chip: string
	/** solid colour for timeline bars and dots */
	bar: string
	soft: string
}

export const PERIODS: Period[] = [
	{ key: "morning", label: "Morning", icon: Sunrise, chip: "bg-amber-50 text-amber-800 border-amber-200", bar: "bg-amber-400", soft: "bg-amber-100" },
	{ key: "midday", label: "Midday", icon: Sun, chip: "bg-sky-50 text-sky-800 border-sky-200", bar: "bg-sky-500", soft: "bg-sky-100" },
	{ key: "evening", label: "Evening", icon: Sunset, chip: "bg-fuchsia-50 text-fuchsia-800 border-fuchsia-200", bar: "bg-fuchsia-500", soft: "bg-fuchsia-100" },
	{ key: "night", label: "Night", icon: Moon, chip: "bg-indigo-50 text-indigo-800 border-indigo-200", bar: "bg-indigo-500", soft: "bg-indigo-100" },
]

/** Colour family by start time: before 11 morning, before 15 midday, before 19 evening, else night. */
export function periodOf(start: string): Period {
	const h = toMinutes(start) / 60
	if (h >= 4 && h < 11) return PERIODS[0]
	if (h >= 11 && h < 15) return PERIODS[1]
	if (h >= 15 && h < 19) return PERIODS[2]
	return PERIODS[3]
}

/** Pieces of a shift on a 0..1440 bar (an overnight shift wraps to the start). */
export function segments(start: string, end: string): { left: number; width: number }[] {
	const [s, e] = span(start, end)
	const pct = (m: number) => (m / DAY) * 100
	if (e <= DAY) return [{ left: pct(s), width: pct(e - s) }]
	return [
		{ left: pct(s), width: pct(DAY - s) },
		{ left: 0, width: pct(e - DAY) },
	]
}
