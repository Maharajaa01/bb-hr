import { onBeforeUnmount, ref, type Ref } from "vue"

export type CameraErrorKind = "unsupported" | "denied" | "notfound" | "busy" | "insecure" | "unknown"

const MESSAGES: Record<CameraErrorKind, string> = {
	unsupported: "This browser cannot use the camera. Use Chrome or Safari on your phone.",
	insecure: "The camera only works over a secure (https) connection.",
	denied: "Camera access is blocked. Allow the camera for this site in your browser settings, then try again.",
	notfound: "No camera was found on this device.",
	busy: "The camera is being used by another app. Close it and try again.",
	unknown: "The camera could not be started. Please try again.",
}

/** Front-camera selfie capture, downscaled to a small JPEG data URL. */
export function useCamera(video: Ref<HTMLVideoElement | null>) {
	const active = ref(false)
	const starting = ref(false)
	const error = ref<{ kind: CameraErrorKind; message: string } | null>(null)
	let stream: MediaStream | null = null

	async function start(): Promise<boolean> {
		error.value = null
		if (!window.isSecureContext) {
			error.value = { kind: "insecure", message: MESSAGES.insecure }
			return false
		}
		if (!navigator.mediaDevices?.getUserMedia) {
			error.value = { kind: "unsupported", message: MESSAGES.unsupported }
			return false
		}
		starting.value = true
		try {
			stream = await navigator.mediaDevices.getUserMedia({
				video: { facingMode: "user", width: { ideal: 720 }, height: { ideal: 720 } },
				audio: false,
			})
			if (video.value) {
				video.value.srcObject = stream
				await video.value.play().catch(() => undefined)
			}
			active.value = true
			return true
		} catch (e) {
			const name = (e as DOMException).name
			const kind: CameraErrorKind =
				name === "NotAllowedError" || name === "SecurityError" ? "denied"
				: name === "NotFoundError" || name === "OverconstrainedError" ? "notfound"
				: name === "NotReadableError" || name === "AbortError" ? "busy"
				: "unknown"
			error.value = { kind, message: MESSAGES[kind] }
			return false
		} finally {
			starting.value = false
		}
	}

	function stop() {
		stream?.getTracks().forEach((t) => t.stop())
		stream = null
		if (video.value) video.value.srcObject = null
		active.value = false
	}

	/** Returns a JPEG data URL, at most `maxSize` px on the long side. */
	function capture(maxSize = 640, quality = 0.75): string | null {
		const v = video.value
		if (!v || !v.videoWidth) return null
		const scale = Math.min(1, maxSize / Math.max(v.videoWidth, v.videoHeight))
		const canvas = document.createElement("canvas")
		canvas.width = Math.round(v.videoWidth * scale)
		canvas.height = Math.round(v.videoHeight * scale)
		const ctx = canvas.getContext("2d")
		if (!ctx) return null
		// mirror so the saved photo matches the preview the person saw
		ctx.translate(canvas.width, 0)
		ctx.scale(-1, 1)
		ctx.drawImage(v, 0, 0, canvas.width, canvas.height)
		return canvas.toDataURL("image/jpeg", quality)
	}

	onBeforeUnmount(stop)
	return { active, starting, error, start, stop, capture }
}
