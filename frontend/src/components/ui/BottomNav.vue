<script setup lang="ts">
import { CalendarRange, Home, IndianRupee, Plus, UserCircle, Users, UsersRound } from "lucide-vue-next"
import { computed } from "vue"
import { useRoute } from "vue-router"

import { useSession } from "@/stores/session"
import { useUi } from "@/stores/ui"

const session = useSession()
const ui = useUi()
const route = useRoute()

// Home · Attendance · [+] · Salary Slip · Account (HR/admin accounts without an employee record get team pages instead)
const left = computed(() =>
	session.isEmployee
		? [{ to: "/", label: "Home", icon: Home }, { to: "/attendance", label: "Attendance", icon: CalendarRange }]
		: [{ to: session.isHr ? "/hr" : "/team", label: "Home", icon: Home }, { to: "/team", label: "Team", icon: Users }],
)
const right = computed(() =>
	session.isEmployee
		? [{ to: "/salary", label: "Salary Slip", icon: IndianRupee }, { to: "/profile", label: "Account", icon: UserCircle }]
		: [{ to: "/directory", label: "Directory", icon: UsersRound }, { to: "/profile", label: "Account", icon: UserCircle }],
)

function isActive(to: string) {
	return to === "/" ? route.path === "/" : route.path === to || route.path.startsWith(`${to}/`)
}
</script>

<template>
	<nav class="fixed inset-x-0 bottom-0 z-30 mx-auto max-w-app border-t border-ink-200 bg-white safe-bottom" aria-label="Main">
		<div class="relative flex h-16 items-stretch">
			<RouterLink v-for="i in left" :key="i.label" :to="i.to" class="flex flex-1 flex-col items-center justify-center gap-0.5 text-[11px] font-medium" :class="isActive(i.to) ? 'text-brand-500' : 'text-ink-500'" :aria-current="isActive(i.to) ? 'page' : undefined">
				<component :is="i.icon" class="h-6 w-6" :stroke-width="1.7" />{{ i.label }}
			</RouterLink>
			<div class="flex w-20 justify-center">
				<span class="absolute -top-7 grid h-[76px] w-[76px] place-items-center rounded-full bg-brand-500/15">
					<button class="grid h-14 w-14 place-items-center rounded-full bg-brand-500 text-white shadow-fab transition active:scale-95 active:bg-brand-600" aria-label="Quick actions" aria-haspopup="dialog" @click="ui.fabOpen = true">
						<Plus class="h-7 w-7" :stroke-width="2.4" />
					</button>
				</span>
			</div>
			<RouterLink v-for="i in right" :key="i.label" :to="i.to" class="flex flex-1 flex-col items-center justify-center gap-0.5 text-[11px] font-medium" :class="isActive(i.to) ? 'text-brand-500' : 'text-ink-500'" :aria-current="isActive(i.to) ? 'page' : undefined">
				<component :is="i.icon" class="h-6 w-6" :stroke-width="1.7" />{{ i.label }}
			</RouterLink>
		</div>
	</nav>
</template>
