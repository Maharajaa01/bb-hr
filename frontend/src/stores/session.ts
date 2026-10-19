import { defineStore } from "pinia"
import { computed, ref } from "vue"

import { call, login as apiLogin, logout as apiLogout } from "@/api/client"
import type { SessionInfo } from "@/api/types"

export const useSession = defineStore("session", () => {
	const info = ref<SessionInfo | null>(null)
	const loaded = ref(false)
	let pending: Promise<void> | null = null

	const user = computed(() => info.value?.user ?? null)
	const employee = computed(() => info.value?.employee ?? null)
	const isLoggedIn = computed(() => !!user.value)
	const isEmployee = computed(() => !!info.value?.roles?.is_employee)
	const isManager = computed(() => !!info.value?.roles?.is_manager)
	const isHr = computed(() => !!info.value?.roles?.is_hr)
	const hasTeamAccess = computed(() => isManager.value || isHr.value)
	const displayName = computed(() => employee.value?.employee_name || user.value?.full_name || "")

	async function load(force = false): Promise<void> {
		if (loaded.value && !force) return
		if (pending && !force) return pending
		pending = (async () => {
			try {
				info.value = await call<SessionInfo>("session.get_session")
			} finally {
				loaded.value = true
				pending = null
			}
		})()
		return pending
	}

	async function login(email: string, password: string): Promise<void> {
		await apiLogin(email, password)
	}

	async function logout(): Promise<void> {
		await apiLogout()
		info.value = { user: null, employee: null }
		// a full reload drops every in-memory record and fetches a fresh CSRF token
		window.location.replace("/bbhr/login")
	}

	return { info, loaded, user, employee, isLoggedIn, isEmployee, isManager, isHr, hasTeamAccess, displayName, load, login, logout }
})
