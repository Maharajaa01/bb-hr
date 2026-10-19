import { describe, expect, it } from "vitest"

import { ApiError, errorFromPayload, parseServerMessages } from "@/api/client"
import { formatDistance, formatHours, formatMoney, formatTime, initials, parseLocal, titleCase } from "@/lib/format"
import { haversine, isValidCoordinate, nearestLocation, withinGeofence } from "@/lib/geo"
import { newRequestId } from "@/lib/id"

describe("geo (mirrors utils/geo.py)", () => {
	it("measures ~100 m for 100 m of latitude", () => {
		const d = haversine(11.0168, 76.9558, 11.0168 + 100 / 111320, 76.9558)
		expect(d).toBeGreaterThan(99)
		expect(d).toBeLessThan(101)
	})
	it("rejects broken coordinates", () => {
		expect(isValidCoordinate(0, 0)).toBe(false)
		expect(isValidCoordinate(91, 10)).toBe(false)
		expect(isValidCoordinate("x", 10)).toBe(false)
		expect(isValidCoordinate(11, 77)).toBe(true)
	})
	it("caps accuracy slack at the tolerance", () => {
		expect(withinGeofence(140, 100, 500, 50)).toBe(true)
		expect(withinGeofence(160, 100, 500, 50)).toBe(false)
		expect(withinGeofence(110, 100, 5, 50)).toBe(false)
	})
	it("picks the nearest office", () => {
		const locs = [
			{ name: "Far", latitude: 11.1, longitude: 76.9558, radius: 100 },
			{ name: "Near", latitude: 11.0169, longitude: 76.9558, radius: 80 },
		]
		const n = nearestLocation(11.0168, 76.9558, locs)
		expect(n?.location.name).toBe("Near")
		expect(n?.radius).toBe(80)
	})
})

describe("format", () => {
	it("parses server datetimes without timezone shift", () => {
		const d = parseLocal("2026-10-16 09:05:00.123")!
		expect([d.getFullYear(), d.getMonth(), d.getDate(), d.getHours(), d.getMinutes()]).toEqual([2026, 9, 16, 9, 5])
		expect(formatTime("2026-10-16 21:45:00")).toBe("9:45 PM")
		expect(formatTime(null)).toBe("—")
	})
	it("formats hours, distance and money", () => {
		expect(formatHours(8.34)).toBe("8h 20m")
		expect(formatHours(0.5)).toBe("30m")
		expect(formatDistance(42.4)).toBe("42 m")
		expect(formatDistance(2500)).toBe("2.5 km")
		expect(formatMoney(25776, "INR")).toContain("25,776")
	})
	it("handles academy-style names", () => {
		expect(initials("S PREETHI")).toBe("PR")
		expect(initials("M R GEETHA")).toBe("GE")
		expect(initials("Maha Raja")).toBe("MR")
		expect(titleCase("M  MADHU MIDHA")).toBe("M Madhu Midha")
	})
})

describe("api errors", () => {
	it("unwraps Frappe _server_messages", () => {
		const raw = JSON.stringify([JSON.stringify({ message: "You are about 400 m from <b>Office</b>.", title: "Outside Office Area" })])
		expect(parseServerMessages(raw)).toEqual([{ title: "Outside Office Area", message: "You are about 400 m from Office." }])
	})
	it("classifies status codes", () => {
		const e = errorFromPayload(403, { exc_type: "PermissionError" })
		expect(e.isPermission).toBe(true)
		expect(e.isNetwork).toBe(false)
		expect(new ApiError("x").isNetwork).toBe(true)
		expect(errorFromPayload(500, null).message).toMatch(/server/)
	})
	it("request ids satisfy the server pattern", () => {
		const id = newRequestId()
		expect(id).toMatch(/^[A-Za-z0-9_-]{8,64}$/)
		expect(newRequestId()).not.toBe(id)
	})
})
