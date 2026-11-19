<script setup lang="ts">
import { ExternalLink, LogOut, Settings } from "lucide-vue-next"
import { computed } from "vue"
import { useRoute } from "vue-router"

import BrandLogo from "@/components/BrandLogo.vue"
import { useNav } from "@/composables/useNav"
import { titleCase } from "@/lib/format"
import { useSession } from "@/stores/session"

import Avatar from "./Avatar.vue"

/** Permanent left navigation on large screens; phones use the drawer and bottom bar instead. */
const session = useSession()
const route = useRoute()
const { items } = useNav()

// the most specific link wins, so /hr/shifts lights up "Shift Planner", not "HR Dashboard"
const activeTo = computed(() => {
	const p = route.path
	const matches = items.value.filter((i) => (i.to === "/" ? p === "/" : p === i.to || p.startsWith(`${i.to}/`)))
	return matches.sort((a, b) => b.to.length - a.to.length)[0]?.to ?? null
})
</script>

<template>
	<aside class="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-ink-200 bg-white lg:flex" aria-label="Main navigation">
		<RouterLink to="/" class="block px-5 pb-4 pt-5" aria-label="BB HRMS home"><BrandLogo class="[&_svg]:h-11 [&_svg]:w-11" /></RouterLink>

		<RouterLink to="/profile" class="mx-3 mb-2 flex items-center gap-3 rounded-2xl bg-brand-50 p-3 hover:bg-brand-100">
			<Avatar :name="session.displayName" :image="session.employee?.image || session.user?.image" size="md" />
			<span class="min-w-0">
				<span class="block truncate text-[14px] font-semibold">{{ titleCase(session.displayName) }}</span>
				<span class="block truncate text-[12px] text-ink-500">{{ titleCase(session.employee?.designation) || (session.isHr ? "HR" : session.user?.name) }}</span>
			</span>
		</RouterLink>

		<nav class="flex-1 space-y-0.5 overflow-y-auto px-3 py-2" aria-label="Pages">
			<RouterLink
				v-for="i in items"
				:key="i.to"
				:to="i.to"
				class="flex h-10 items-center gap-3 rounded-xl px-3 text-[14px] transition"
				:class="activeTo === i.to ? 'bg-brand-500 font-medium text-white shadow-fab' : 'text-ink-700 hover:bg-ink-50'"
				:aria-current="activeTo === i.to ? 'page' : undefined"
			>
				<component :is="i.icon" class="h-[18px] w-[18px]" :stroke-width="activeTo === i.to ? 2 : 1.6" />{{ i.label }}
			</RouterLink>
		</nav>

		<div class="space-y-0.5 border-t border-ink-200 p-3">
			<a v-if="session.info?.desk_access" href="/app" class="flex h-10 items-center gap-3 rounded-xl px-3 text-[14px] text-ink-700 hover:bg-ink-50"><ExternalLink class="h-[18px] w-[18px]" :stroke-width="1.6" />Open HR Desk</a>
			<a v-if="session.isHr && session.info?.desk_access" href="/app/bb-hr-settings" class="flex h-10 items-center gap-3 rounded-xl px-3 text-[14px] text-ink-700 hover:bg-ink-50"><Settings class="h-[18px] w-[18px]" :stroke-width="1.6" />Settings</a>
			<button class="flex h-10 w-full items-center gap-3 rounded-xl px-3 text-[14px] text-danger hover:bg-danger-soft/60" @click="session.logout()"><LogOut class="h-[18px] w-[18px]" :stroke-width="1.6" />Logout</button>
		</div>
	</aside>
</template>
