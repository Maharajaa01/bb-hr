<script setup lang="ts">
import { useOnline } from "@vueuse/core"
import { ChevronRight, Download, ExternalLink, LogOut, Smartphone, WifiOff } from "lucide-vue-next"
import { computed } from "vue"

import AppBar from "@/components/ui/AppBar.vue"
import AppButton from "@/components/ui/AppButton.vue"
import Avatar from "@/components/ui/Avatar.vue"
import { useNav } from "@/composables/useNav"
import { formatDate, titleCase } from "@/lib/format"
import { canInstall, isStandalone, promptInstall } from "@/lib/pwa"
import { useSession } from "@/stores/session"

const session = useSession()
const online = useOnline()
const { items } = useNav()
const standalone = isStandalone()
const ios = /iPhone|iPad|iPod/i.test(navigator.userAgent)
const menu = computed(() => items.value.filter((i) => i.to !== "/profile" && i.to !== "/"))
const active = computed(() => session.employee?.status === "Active")
</script>

<template>
	<div>
		<AppBar title="My Profile" back="/">
			<template #actions>
				<button class="grid h-11 w-11 place-items-center rounded-full hover:bg-white/15" aria-label="Logout" @click="session.logout()"><LogOut class="h-5 w-5" /></button>
			</template>
		</AppBar>

		<section class="relative overflow-hidden rounded-xl border border-ink-200 bg-white p-4">
			<span class="absolute -left-8 -top-8 h-24 w-24 rounded-[28px] bg-brand-100" aria-hidden="true" />
			<span class="absolute -bottom-10 -right-10 h-24 w-24 rounded-full bg-warning/80" aria-hidden="true" />
			<div class="relative flex items-center gap-4">
				<Avatar :name="session.displayName" :image="session.employee?.image || session.user?.image" size="xl" square />
				<div class="min-w-0 flex-1">
					<p class="truncate text-lg font-semibold">{{ titleCase(session.displayName) }}</p>
					<p class="text-[13px] text-ink-500">{{ session.employee?.name || session.user?.name }}</p>
					<p v-if="session.employee?.designation" class="truncate text-[13px] text-ink-500">{{ titleCase(session.employee.designation) }}</p>
				</div>
				<span v-if="session.employee" class="self-start text-[13px] font-medium" :class="active ? 'text-success' : 'text-danger'">{{ session.employee.status }} ●</span>
			</div>
			<dl v-if="session.employee" class="relative mt-4 grid grid-cols-2 gap-3 text-[13px]">
				<div><dt class="text-ink-500">Department</dt><dd class="font-medium">{{ session.employee.department?.replace(/ - BBA$/, "") || "—" }}</dd></div>
				<div><dt class="text-ink-500">Joined</dt><dd class="font-medium">{{ formatDate(session.employee.date_of_joining) }}</dd></div>
			</dl>
		</section>

		<nav class="mt-3" aria-label="Pages">
			<RouterLink v-for="i in menu" :key="i.to" :to="i.to" class="flex h-12 items-center gap-4 border-b border-ink-100 px-1 text-[15px] hover:bg-ink-50">
				<component :is="i.icon" class="h-5 w-5 text-ink-600" :stroke-width="1.5" /><span class="flex-1">{{ i.label }}</span><ChevronRight class="h-5 w-5 text-ink-400" />
			</RouterLink>
			<a v-if="session.info?.desk_access" href="/app" class="flex h-12 items-center gap-4 border-b border-ink-100 px-1 text-[15px] hover:bg-ink-50">
				<ExternalLink class="h-5 w-5 text-ink-600" :stroke-width="1.5" /><span class="flex-1">Open HR Desk</span><ChevronRight class="h-5 w-5 text-ink-400" />
			</a>
		</nav>

		<section class="mt-4 space-y-2.5">
			<div v-if="!online" class="flex items-center gap-3 rounded-xl bg-danger-soft p-3 text-[14px] text-danger"><WifiOff class="h-5 w-5" />Offline - live data and check-in are unavailable</div>
			<div class="card flex items-center gap-3 p-3">
				<Smartphone class="h-5 w-5 text-ink-500" />
				<p class="flex-1 text-[14px]">
					<template v-if="standalone">Installed as an app</template>
					<template v-else-if="canInstall">Install BB HR for one-tap check-in</template>
					<template v-else-if="ios">On iPhone: Share → "Add to Home Screen"</template>
					<template v-else>Browser menu → "Install app"</template>
				</p>
				<AppButton v-if="canInstall && !standalone" size="sm" @click="promptInstall"><Download class="h-4 w-4" />Install</AppButton>
			</div>
		</section>
	</div>
</template>
