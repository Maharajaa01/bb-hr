import { onBeforeUnmount, ref } from "vue"

export type GeoErrorKind = "unsupported" | "denied" | "unavailable" | "timeout" | "insecure"

export interface GeoFix {
	latitude: number
	longitude: number
	accuracy: number
	timestamp: number
}

const MESSAGES: Record<GeoErrorKind, string> = {
	unsupported: "This browser cannot share your location. Use Chrome or Safari on your phone.",
	insecure: "Location only works over a secure (https) connection.",
	denied: "Location access is blocked. Allow location for this site in your browser settings, then try again.",
	unavailable: "Your location is unavailable. Turn on GPS / Location services and try again.",
	timeout: "Getting your location took too long. Move near a window or outdoors and try again.",
}

/**
 * Watch the position for up to `maxWaitMs`, keeping the most accurate fix.
 * Stops early once a fix is at least as good as `goodEnough` metres.
 */
export function useGeolocation(opts: { maxWaitMs?: number; goodEnough?: number } = {}) {
	const fix = ref<GeoFix | null>(null)
	const error = ref<{ kind: GeoErrorKind; message: string } | null>(null)
	const locating = ref(false)
	let watchId: number | null = null
	let timer: ReturnType<typeof setTimeout> | null = null

	function stop() {
		if (watchId !== null) navigator.geolocation.clearWatch(watchId)
		if (timer) clearTimeout(timer)
		watchId = null
		timer = null
		locating.value = false
	}

	function fail(kind: GeoErrorKind) {
		error.value = { kind, message: MESSAGES[kind] }
		stop()
	}

	function locate(): Promise<GeoFix | null> {
		stop()
		error.value = null
		fix.value = null
		if (!window.isSecureContext) {
			fail("insecure")
			return Promise.resolve(null)
		}
		if (!("geolocation" in navigator)) {
			fail("unsupported")
			return Promise.resolve(null)
		}
		locating.value = true
		const maxWait = opts.maxWaitMs ?? 15000
		const goodEnough = opts.goodEnough ?? 25

		return new Promise((resolve) => {
			const finish = () => {
				const result = fix.value
				if (!result && !error.value) error.value = { kind: "timeout", message: MESSAGES.timeout }
				stop()
				resolve(result)
			}
			timer = setTimeout(finish, maxWait)
			watchId = navigator.geolocation.watchPosition(
				(pos) => {
					const next: GeoFix = {
						latitude: pos.coords.latitude,
						longitude: pos.coords.longitude,
						accuracy: pos.coords.accuracy,
						timestamp: pos.timestamp,
					}
					if (!fix.value || next.accuracy <= fix.value.accuracy) fix.value = next
					if (next.accuracy <= goodEnough) finish()
				},
				(err) => {
					// keep any fix we already have; only fail when we have nothing
					if (fix.value) return finish()
					const kind: GeoErrorKind = err.code === 1 ? "denied" : err.code === 2 ? "unavailable" : "timeout"
					fail(kind)
					resolve(null)
				},
				{ enableHighAccuracy: true, maximumAge: 0, timeout: maxWait },
			)
		})
	}

	onBeforeUnmount(stop)
	return { fix, error, locating, locate, stop }
}
