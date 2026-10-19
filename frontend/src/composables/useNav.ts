import { computed } from "vue"

import { NAV, type NavItem } from "@/layouts/navigation"
import { useSession } from "@/stores/session"

export function useNav() {
	const session = useSession()
	function allowed(item: NavItem) {
		if (item.access === "employee") return session.isEmployee
		if (item.access === "team") return session.hasTeamAccess
		if (item.access === "hr") return session.isHr
		return true
	}
	const items = computed(() => NAV.filter(allowed))
	/** "+" action sheet: the quick actions this user can take. */
	const actions = computed(() => items.value.filter((i) => ["/check-in", "/holidays", "/attendance", "/team", "/exceptions", "/hr"].includes(i.to)).slice(0, 5))
	return { items, actions, allowed }
}
