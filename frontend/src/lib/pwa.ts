/**
 * Service worker registration and the install prompt.
 *
 * The worker lives at /bbhr_sw.js (site root) so it can control /bbhr/*.
 * A new worker never takes over silently: it waits until the user taps "Update",
 * so nobody loses a half-finished check-in to a background reload.
 */
import { ref } from "vue"

export const updateReady = ref(false)
export const canInstall = ref(false)
let waiting: ServiceWorker | null = null
let deferredPrompt: (Event & { prompt: () => Promise<void>; userChoice: Promise<{ outcome: string }> }) | null = null

export function registerServiceWorker(): void {
	if (!("serviceWorker" in navigator) || import.meta.env.DEV) return
	window.addEventListener("load", async () => {
		try {
			const reg = await navigator.serviceWorker.register("/bbhr_sw.js", { scope: "/bbhr/" })
			const track = (w: ServiceWorker | null) => {
				if (!w) return
				w.addEventListener("statechange", () => {
					if (w.state === "installed" && navigator.serviceWorker.controller) {
						waiting = w
						updateReady.value = true
					}
				})
			}
			if (reg.waiting && navigator.serviceWorker.controller) {
				waiting = reg.waiting
				updateReady.value = true
			}
			reg.addEventListener("updatefound", () => track(reg.installing))
			// check for a new build every 30 minutes while the app stays open
			setInterval(() => reg.update().catch(() => undefined), 30 * 60 * 1000)
		} catch (e) {
			console.warn("BB HR: service worker registration failed", e)
		}
	})
	let reloading = false
	navigator.serviceWorker.addEventListener("controllerchange", () => {
		if (reloading) return
		reloading = true
		window.location.reload()
	})
}

export function applyUpdate(): void {
	waiting?.postMessage({ type: "SKIP_WAITING" })
}

window.addEventListener("beforeinstallprompt", (e) => {
	e.preventDefault()
	deferredPrompt = e as typeof deferredPrompt
	canInstall.value = true
})
window.addEventListener("appinstalled", () => {
	canInstall.value = false
	deferredPrompt = null
})

export async function promptInstall(): Promise<boolean> {
	if (!deferredPrompt) return false
	await deferredPrompt.prompt()
	const choice = await deferredPrompt.userChoice
	deferredPrompt = null
	canInstall.value = false
	return choice.outcome === "accepted"
}

export function isStandalone(): boolean {
	return window.matchMedia?.("(display-mode: standalone)").matches || (navigator as { standalone?: boolean }).standalone === true
}
