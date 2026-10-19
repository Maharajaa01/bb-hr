import { defineStore } from "pinia"
import { ref } from "vue"

/** Shell chrome state: side drawer and the "+" action sheet. */
export const useUi = defineStore("ui", () => {
	const drawerOpen = ref(false)
	const fabOpen = ref(false)
	return { drawerOpen, fabOpen }
})
