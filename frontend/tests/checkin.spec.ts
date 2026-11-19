import { flushPromises, mount } from "@vue/test-utils"
import { createPinia } from "pinia"
import { beforeEach, describe, expect, it, vi } from "vitest"
import type { Component } from "vue"
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

let status: typeof STATUS & { rules: { face?: { enabled: boolean; liveness: boolean; enrolled: boolean } } } = STATUS

async function mountView(stubs: Record<string, Component> = {}) {
	const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/", component: { template: "<div/>" } }, { path: "/check-in", component: CheckIn }] })
	await router.push("/check-in")
	const wrapper = mount(CheckIn, { global: { plugins: [createPinia(), router], directives: { motion: {} }, stubs } })
	await flushPromises()
	await new Promise((r) => setTimeout(r, 5))
	await flushPromises()
	return wrapper
}

function confirmButton(wrapper: Awaited<ReturnType<typeof mountView>>) {
	return wrapper.findAll("button").find((b) => /^(Confirm|Retry) /.test(b.attributes("aria-label") ?? ""))!
}

beforeEach(() => {
	status = STATUS
	punchBodies.length = 0
	Object.defineProperty(window, "isSecureContext", { configurable: true, value: true })
	Object.defineProperty(navigator, "onLine", { configurable: true, value: true })
	setPosition(11.0168 + 20 / 111320, 76.9558, 12) // ~20 m from the office
	vi.stubGlobal("fetch", vi.fn(async (url: string, init: RequestInit) => {
		if (url.includes("attendance.get_status")) return json({ message: status })
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

	describe("with face verification", () => {
		const SCAN = { token: "tok_123456789", front: ["data:image/jpeg;base64,AAA"], turn: ["data:image/jpeg;base64,BBB"], preview: "data:image/jpeg;base64,AAA" }
		const reset = vi.fn()
		/** Stands in for the camera: "scanning" just emits a finished scan. */
		const FaceScanStub = {
			props: ["modelValue", "enrolled"],
			emits: ["update:modelValue"],
			setup(_p: unknown, { expose }: { expose: (e: Record<string, unknown>) => void }) {
				expose({ reset })
			},
			template: `<button data-test="scan" @click="$emit('update:modelValue', ${JSON.stringify(SCAN).replace(/"/g, "'")})">{{ enrolled ? 'enrolled' : 'first time' }}</button>`,
		}

		beforeEach(() => {
			reset.mockClear()
			status = { ...STATUS, rules: { ...STATUS.rules, require_photo: true, face: { enabled: true, liveness: true, enrolled: false } } }
		})

		it("asks for a face scan, not a selfie, before confirming", async () => {
			const w = await mountView({ FaceScan: FaceScanStub })
			expect(w.text()).toContain("Set up face check-in to continue.")
			expect(w.text()).not.toContain("Selfie required")
			expect(w.find("[data-test=scan]").text()).toBe("first time")
			expect(confirmButton(w).attributes("disabled")).toBeDefined()
		})

		it("sends the scan with the punch and reports a first-time enrolment", async () => {
			punchHandler = () => json({ message: { ok: true, replayed: false, checkin: "EMP-CKIN-1", log_type: "IN", time: "2026-10-16 09:00:05", location: "Main Campus", distance: 20, attendance: null, warning: null, face_status: "Enrolled", message: "Checked in at 09:00 AM" } })
			const w = await mountView({ FaceScan: FaceScanStub })
			await w.find("[data-test=scan]").trigger("click")
			expect(confirmButton(w).attributes("disabled")).toBeUndefined()
			await confirmButton(w).trigger("click")
			await flushPromises()
			expect(punchBodies[0]).toMatchObject({ face: { token: SCAN.token, front: SCAN.front, turn: SCAN.turn } })
			expect(punchBodies[0].photo).toBeUndefined()
			expect(punchBodies[0].face).not.toHaveProperty("preview")
			expect(w.text()).toContain("Face check-in is set up")
		})

		it("a face rejection discards the spent scan", async () => {
			punchHandler = () =>
				json({ exc_type: "ValidationError", _server_messages: JSON.stringify([JSON.stringify({ title: "Face Not Verified", message: "Your face does not match." })]) }, 417)
			const w = await mountView({ FaceScan: FaceScanStub })
			await w.find("[data-test=scan]").trigger("click")
			await confirmButton(w).trigger("click")
			await flushPromises()
			expect(w.text()).toContain("Face Not Verified")
			expect(reset).toHaveBeenCalled()
		})
	})
})
