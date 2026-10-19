/**
 * Thin, typed wrapper over Frappe whitelisted methods.
 *
 * Endpoints live under bb_academy_hrms.api.*, so callers name them as
 * "attendance.punch" rather than repeating the module path.
 */

const PREFIX = "/api/method/bb_academy_hrms.api."

export interface ServerMessage {
	title?: string
	message: string
}

export class ApiError extends Error {
	status: number
	excType: string
	title: string
	messages: ServerMessage[]

	constructor(message: string, opts: { status?: number; excType?: string; title?: string; messages?: ServerMessage[] } = {}) {
		super(message)
		this.name = "ApiError"
		this.status = opts.status ?? 0
		this.excType = opts.excType ?? ""
		this.title = opts.title ?? ""
		this.messages = opts.messages ?? []
	}

	/** No HTTP response at all - offline, DNS, server down. */
	get isNetwork(): boolean {
		return this.status === 0
	}

	get isPermission(): boolean {
		return this.status === 403 || /PermissionError/.test(this.excType)
	}

	get isNotFound(): boolean {
		return this.status === 404 || /DoesNotExistError/.test(this.excType)
	}
}

function csrfToken(): string | null {
	const t = window.csrf_token
	return t && t !== "None" && !t.startsWith("{{") ? t : null
}

function htmlToText(html: string): string {
	const div = document.createElement("div")
	div.innerHTML = html.replace(/<br\s*\/?>/gi, "\n")
	return (div.textContent || "").trim()
}

/** Frappe returns user-facing errors as JSON strings inside `_server_messages`. */
export function parseServerMessages(raw: unknown): ServerMessage[] {
	if (typeof raw !== "string" || !raw) return []
	try {
		const list = JSON.parse(raw) as unknown[]
		return list
			.map((entry) => {
				const parsed = (typeof entry === "string" ? JSON.parse(entry) : entry) as { message?: string; title?: string }
				return { title: parsed.title, message: htmlToText(String(parsed.message ?? "")) }
			})
			.filter((m) => m.message)
	} catch {
		return []
	}
}

export function errorFromPayload(status: number, payload: Record<string, unknown> | null): ApiError {
	const messages = parseServerMessages(payload?._server_messages)
	const excType = String(payload?.exc_type ?? "")
	const first = messages[messages.length - 1]
	let message = first?.message
	if (!message) {
		if (status === 403) message = "You do not have permission to do that."
		else if (status === 404) message = "That record could not be found."
		else if (status === 417 || status === 400) message = "The request was not accepted."
		else if (status >= 500) message = "The server ran into a problem. Please try again shortly."
		else message = "Something went wrong."
	}
	return new ApiError(message, { status, excType, title: first?.title, messages })
}

export interface CallOptions {
	method?: "GET" | "POST"
	signal?: AbortSignal
}

export async function call<T>(name: string, args: Record<string, unknown> = {}, opts: CallOptions = {}): Promise<T> {
	const method = opts.method ?? "GET"
	const headers: Record<string, string> = { Accept: "application/json", "X-Requested-With": "XMLHttpRequest" }
	let url = PREFIX + name
	const init: RequestInit = { method, headers, credentials: "same-origin", signal: opts.signal, cache: "no-store" }

	if (method === "GET") {
		const params = new URLSearchParams()
		for (const [k, v] of Object.entries(args)) {
			if (v !== undefined && v !== null && v !== "") params.set(k, String(v))
		}
		const qs = params.toString()
		if (qs) url += `?${qs}`
	} else {
		headers["Content-Type"] = "application/json"
		const token = csrfToken()
		if (token) headers["X-Frappe-CSRF-Token"] = token
		init.body = JSON.stringify(args)
	}

	let response: Response
	try {
		response = await fetch(url, init)
	} catch (e) {
		if ((e as Error).name === "AbortError") throw e
		throw new ApiError("Cannot reach the server. Check your connection and try again.")
	}

	let payload: Record<string, unknown> | null = null
	const text = await response.text()
	if (text) {
		try {
			payload = JSON.parse(text)
		} catch {
			payload = null
		}
	}
	if (!response.ok) {
		if (response.status === 403 && /Login to access|session_expired/i.test(String(payload?.exception ?? "") + String(payload?.session_expired ?? ""))) {
			// the session ended (logout elsewhere, expiry): go back to sign-in rather than show "not allowed"
			const here = window.location.pathname.replace(/^\/bbhr/, "") || "/"
			if (!here.startsWith("/login")) window.location.replace(`/bbhr/login?redirect=${encodeURIComponent(here)}`)
		}
		throw errorFromPayload(response.status, payload)
	}
	return (payload?.message ?? null) as T
}

/** URL for a GET endpoint that returns a file (PDF, image). */
export function fileUrl(name: string, args: Record<string, string>): string {
	return `${PREFIX}${name}?${new URLSearchParams(args).toString()}`
}

export async function login(usr: string, pwd: string): Promise<void> {
	let response: Response
	try {
		response = await fetch("/api/method/login", {
			method: "POST",
			credentials: "same-origin",
			headers: { "Content-Type": "application/json", Accept: "application/json" },
			body: JSON.stringify({ usr, pwd }),
		})
	} catch {
		throw new ApiError("Cannot reach the server. Check your connection and try again.")
	}
	if (!response.ok) {
		const payload = await response.json().catch(() => null)
		if (response.status === 401) throw new ApiError("Incorrect email or password.", { status: 401 })
		throw errorFromPayload(response.status, payload)
	}
}

export async function logout(): Promise<void> {
	const token = csrfToken()
	await fetch("/api/method/logout", {
		method: "POST",
		credentials: "same-origin",
		headers: token ? { "X-Frappe-CSRF-Token": token } : {},
	}).catch(() => undefined)
}
