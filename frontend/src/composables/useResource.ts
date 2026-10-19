import { onBeforeUnmount, ref, shallowRef, type Ref } from "vue"

import { ApiError } from "@/api/client"

/**
 * Load-once-and-reload helper with loading/error state.
 * A newer load aborts an older one, so fast filter changes never show stale data.
 */
export function useResource<T>(loader: (signal: AbortSignal) => Promise<T>, opts: { immediate?: boolean } = {}) {
	const data = shallowRef<T | null>(null) as Ref<T | null>
	const error = ref<ApiError | null>(null)
	const loading = ref(false)
	let controller: AbortController | null = null

	async function reload(): Promise<void> {
		controller?.abort()
		const mine = new AbortController()
		controller = mine
		loading.value = true
		error.value = null
		try {
			const result = await loader(mine.signal)
			if (controller === mine) data.value = result
		} catch (e) {
			if ((e as Error).name === "AbortError") return
			if (controller === mine) error.value = e instanceof ApiError ? e : new ApiError(String((e as Error).message || e))
		} finally {
			if (controller === mine) loading.value = false
		}
	}

	onBeforeUnmount(() => controller?.abort())
	if (opts.immediate !== false) void reload()
	return { data, error, loading, reload }
}
