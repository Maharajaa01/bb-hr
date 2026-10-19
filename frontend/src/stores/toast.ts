import { defineStore } from "pinia"
import { ref } from "vue"

export type ToastTone = "success" | "error" | "info" | "warning"
export interface Toast {
	id: number
	tone: ToastTone
	title: string
	message?: string
}

export const useToasts = defineStore("toasts", () => {
	const items = ref<Toast[]>([])
	let seq = 0

	function push(tone: ToastTone, title: string, message?: string, timeout = 4500) {
		const id = ++seq
		items.value.push({ id, tone, title, message })
		if (timeout) setTimeout(() => dismiss(id), timeout)
		return id
	}

	function dismiss(id: number) {
		items.value = items.value.filter((t) => t.id !== id)
	}

	return {
		items,
		push,
		dismiss,
		success: (t: string, m?: string) => push("success", t, m),
		error: (t: string, m?: string) => push("error", t, m, 7000),
		info: (t: string, m?: string) => push("info", t, m),
		warning: (t: string, m?: string) => push("warning", t, m, 7000),
	}
})
