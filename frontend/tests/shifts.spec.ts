import { describe, expect, it } from "vitest"

import { datesOverlap, duration, isOvernight, periodOf, segments, time12, timesOverlap } from "@/lib/shifts"

describe("shift overlap (mirrors api/shifts.py)", () => {
	it("flags shifts that share time", () => {
		expect(timesOverlap({ start: "06:00", end: "07:30" }, { start: "07:00", end: "09:00" })).toBe(true)
		expect(timesOverlap({ start: "16:30", end: "21:30" }, { start: "06:15", end: "21:30" })).toBe(true)
	})
	it("lets back-to-back shifts touch", () => {
		expect(timesOverlap({ start: "06:00", end: "07:30" }, { start: "07:30", end: "09:00" })).toBe(false)
		expect(timesOverlap({ start: "06:00", end: "07:30" }, { start: "16:30", end: "21:30" })).toBe(false)
	})
	it("handles shifts past midnight", () => {
		expect(timesOverlap({ start: "22:00", end: "06:00" }, { start: "05:00", end: "07:00" })).toBe(true)
		expect(timesOverlap({ start: "22:00", end: "02:00" }, { start: "05:00", end: "07:00" })).toBe(false)
		expect(isOvernight("22:00", "06:00")).toBe(true)
	})
	it("compares date ranges with open ends", () => {
		expect(datesOverlap("2026-11-01", null, "2026-12-01", "2026-12-31")).toBe(true)
		expect(datesOverlap("2026-11-01", "2026-11-30", "2026-12-01", null)).toBe(false)
		expect(datesOverlap("2026-11-01", "2026-11-30", "2026-11-30", null)).toBe(true)
	})
})

describe("shift display", () => {
	it("formats 12-hour times and lengths", () => {
		expect(time12("06:15")).toBe("6:15 AM")
		expect(time12("00:00")).toBe("12:00 AM")
		expect(time12("21:30")).toBe("9:30 PM")
		expect(duration("06:00", "07:30")).toBe("1 h 30 m")
		expect(duration("22:00", "06:00")).toBe("8 h")
	})
	it("colours by start time", () => {
		expect(periodOf("06:00").key).toBe("morning")
		expect(periodOf("12:00").key).toBe("midday")
		expect(periodOf("16:30").key).toBe("evening")
		expect(periodOf("21:00").key).toBe("night")
		expect(periodOf("02:00").key).toBe("night")
	})
	it("splits overnight bars", () => {
		expect(segments("06:00", "12:00")).toEqual([{ left: 25, width: 25 }])
		expect(segments("18:00", "06:00")).toEqual([{ left: 75, width: 25 }, { left: 0, width: 25 }])
	})
})
