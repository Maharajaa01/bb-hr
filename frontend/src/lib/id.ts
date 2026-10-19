/** Idempotency key for one punch attempt (server accepts [A-Za-z0-9_-]{8,64}). */
export function newRequestId(): string {
	if (typeof crypto.randomUUID === "function") return crypto.randomUUID().replace(/-/g, "")
	const bytes = new Uint8Array(16)
	crypto.getRandomValues(bytes)
	return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")
}

/** A short, stable label for the device in the check-in log. Never includes personal data. */
export function deviceLabel(): string {
	const ua = navigator.userAgent
	const os = /Android/i.test(ua) ? "Android" : /iPhone|iPad|iPod/i.test(ua) ? "iOS" : /Windows/i.test(ua) ? "Windows" : /Mac OS/i.test(ua) ? "macOS" : "Other"
	const standalone = window.matchMedia?.("(display-mode: standalone)").matches ? "app" : "browser"
	return `${os} ${standalone}`
}
