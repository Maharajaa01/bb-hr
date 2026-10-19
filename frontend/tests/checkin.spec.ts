import { flushPromises, mount } from "@vue/test-utils"
import { createPinia } from "pinia"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { createMemoryHistory, createRouter } from "vue-router"

import CheckIn from "@/views/CheckIn.vue"

const STATUS = {
	employee: "HR-EMP-00001",
	employee_name: "Test Staff",
	date: "2026-10-16",
	server_time: "2026-10-16 09:00:00",
	logs: [],
	checked_in: false,
	next_action: "IN",
	first_in: null,
	last_out: null,
	worked_hours: 0,
	late_minutes: 0,
	shift: {},
	holiday: null,
	attendance: null,
	rules: {
		geofence: true,
		require_photo: false,
		max_accuracy: 200,
		accuracy_tolerance: 50,
		min_gap_seconds: 60,
		locations: [{ name: "Main Campus", latitude: 11.0168, longitude: 76.9558, radius: 100 }],
	},
}

type Handler = (url: string, init: RequestInit) => Response | Promise<Response>
let punchHandler: Handler
const punchBodies: Record<string, unknown>[] = []

function json(body: unknown, status = 200) {
	return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } })
}

function setPosition(lat: number, lon: number, accuracy: number) {
	Object.defineProperty(navigator, "geolocation", {
		configurable: true,
		value: {
			watchPosition: (ok: PositionCallback) => {
				setTimeout(() => ok({ coords: { latitude: lat, longitude: lon, accuracy }, timestamp: Date.now() } as GeolocationPosition), 0)
				return 1
			},
			clearWatch: () => undefined,
		},
	})
}

async function mountView() {
	const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/", component: { template: "<div/>" } }, { path: "/check-in", component: CheckIn }] })
	await router.push("/check-in")
	const wrapper = mount(CheckIn, { global: { plugins: [createPinia(), router], directives: { motion: {} } } })
	await flushPromises()
	await new Promise((r) => setTimeout(r, 5))
	await flushPromises()
	return wrapper
}

function confirmButton(wrapper: Awaited<ReturnType<typeof mountView>>) {
	return wrapper.findAll("button").find((b) => /^(Confirm|Retry) /.test(b.attributes("aria-label") ?? ""))!
}

beforeEach(() => {
	punchBodies.length = 0
	Object.defineProperty(window, "isSecureContext", { configurable: true, value: true })
	Object.defineProperty(navigator, "onLine", { configurable: true, value: true })
	setPosition(11.0168 + 20 / 111320, 76.9558, 12) // ~20 m from the office
	vi.stubGlobal("fetch", vi.fn(async (url: string, init: RequestInit) => {
		if (url.includes("attendance.get_status")) return json({ message: STATUS })
		if (url.includes("attendance.punch")) {
			punchBodies.push(JSON.parse(String(init.body)))
			return punchHandler(url, init)
		}
		return json({ message: null })
	}))
})

describe("CheckIn", () => {
	it("enables confirm only inside the geofence", async () => {
		setPosition(11.0168 + 500 / 111320, 76.9558, 10)
		const w = await mountView()
		expect(w.text()).toContain("Outside the office area")
		expect(confirmButton(w).attributes("disabled")).toBeDefined()
	})

	it("shows success only after the server returns the created record", async () => {
		punchHandler = () => json({ message: { ok: true, replayed: false, checkin: "EMP-CKIN-1", log_type: "IN", time: "2026-10-16 09:00:05", location: "Main Campus", distance: 20, attendance: "HR-ATT-1", warning: null, message: "Checked in at 09:00 AM" } })
		const w = await mountView()
		expect(w.text()).toContain("Inside Main Campus")
		await confirmButton(w).trigger("click")
		await flushPromises()
		expect(w.text()).toContain("Checked in at 09:00 AM")
		expect(w.text()).toContain("EMP-CKIN-1")
		expect(punchBodies[0]).toMatchObject({ log_type: "IN", accuracy: 12 })
	})

	it("never reports success for a malformed reply", async () => {
		punchHandler = () => json({ message: { ok: true } })
		const w = await mountView()
		await confirmButton(w).trigger("click")
		await flushPromises()
		expect(w.text()).not.toContain("Checked in at")
		expect(w.text()).toContain("couldn't confirm")
	})

	it("network failure is 'unconfirmed' and the retry reuses the same request id", async () => {
		punchHandler = () => Promise.reject(new TypeError("Failed to fetch"))
		const w = await mountView()
		await confirmButton(w).trigger("click")
		await flushPromises()
		expect(w.text()).toContain("couldn't confirm")
		expect(w.text()).not.toContain("Checked in at")

		punchHandler = () => json({ message: { ok: true, replayed: true, checkin: "EMP-CKIN-1", log_type: "IN", time: "2026-10-16 09:00:05", location: "Main Campus", distance: 20, attendance: null, warning: null, message: "Checked in at 09:00 AM" } })
		await confirmButton(w).trigger("click")
		await flushPromises()
		expect(punchBodies).toHaveLength(2)
		expect(punchBodies[1].request_id).toBe(punchBodies[0].request_id)
		expect(w.text()).toContain("Checked in at 09:00 AM")
	})

	it("a server rejection shows the reason and uses a fresh id next time", async () => {
		punchHandler = () =>
			json({ exc_type: "ValidationError", _server_messages: JSON.stringify([JSON.stringify({ title: "Already Checked In", message: "You are already checked in." })]) }, 417)
		const w = await mountView()
		await confirmButton(w).trigger("click")
		await flushPromises()
		expect(w.text()).toContain("Already Checked In")
		await confirmButton(w).trigger("click")
		await flushPromises()
		expect(punchBodies[1].request_id).not.toBe(punchBodies[0].request_id)
	})

	it("refuses to submit while offline", async () => {
		Object.defineProperty(navigator, "onLine", { configurable: true, value: false })
		punchHandler = () => json({ message: null })
		const w = await mountView()
		expect(confirmButton(w).attributes("disabled")).toBeDefined()
		expect(w.text()).toContain("You're offline")
		expect(punchBodies).toHaveLength(0)
	})
})
