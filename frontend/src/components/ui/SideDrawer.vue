<script setup lang="ts">
import { LogOut, Settings, X } from "lucide-vue-next"
import { watch } from "vue"
import { useRoute } from "vue-router"

import { useNav } from "@/composables/useNav"
import { titleCase } from "@/lib/format"
import { useSession } from "@/stores/session"
import { useUi } from "@/stores/ui"

import Avatar from "./Avatar.vue"

const ui = useUi()
const session = useSession()
const route = useRoute()
const { items } = useNav()
watch(() => ui.drawerOpen, (v) => (document.body.style.overflow = v ? "hidden" : ""))
watch(() => route.fullPath, () => (ui.drawerOpen = false))
</script>

<template>
	<Teleport to="body">
		<Transition name="drawer">
			<div v-if="ui.drawerOpen" class="fixed inset-0 z-40 bg-black/40" @click.self="ui.drawerOpen = false" @keydown.esc="ui.drawerOpen = false">
				<aside class="flex h-full w-[250px] flex-col bg-white shadow-lift safe-top" role="dialog" aria-modal="true" aria-label="Menu">
					<div class="flex items-start gap-3 border-b border-ink-200 p-4">
						<Avatar :name="session.displayName" :image="session.employee?.image || session.user?.image" size="md" />
						<div class="min-w-0 flex-1">
							<p class="truncate font-semibold">{{ titleCase(session.displayName) }}</p>
							<p class="truncate text-[13px] text-ink-500">{{ titleCase(session.employee?.designation) || session.user?.name }}</p>
						</div>
						<button class="-m-1 grid h-9 w-9 place-items-center rounded-full text-brand-500 hover:bg-brand-50" aria-label="Close menu" @click="ui.drawerOpen = false"><X class="h-5 w-5" /></button>
					</div>
					<nav class="flex-1 overflow-y-auto py-1" aria-label="Menu">
						<RouterLink v-for="i in items" :key="i.to" :to="i.to" class="flex h-11 items-center gap-3 px-4 text-[15px] hover:bg-ink-50" :class="route.path === i.to ? 'text-brand-500' : 'text-ink-900'">
							<component :is="i.icon" class="h-5 w-5 text-ink-600" :class="route.path === i.to ? '!text-brand-500' : ''" :stroke-width="1.5" />{{ i.label }}
						</RouterLink>
					</nav>
					<div class="border-t border-ink-200 py-1 safe-bottom">
						<a v-if="session.isHr && session.info?.desk_access" href="/app/bb-hr-settings" class="flex h-11 items-center gap-3 px-4 text-[15px] hover:bg-ink-50"><Settings class="h-5 w-5 text-ink-600" :stroke-width="1.5" />Settings</a>
						<RouterLink v-else to="/profile" class="flex h-11 items-center gap-3 px-4 text-[15px] hover:bg-ink-50"><Settings class="h-5 w-5 text-ink-600" :stroke-width="1.5" />Settings</RouterLink>
						<div class="mx-4 border-t border-ink-200" />
						<button class="flex h-11 w-full items-center gap-3 px-4 text-[15px] text-danger hover:bg-danger-soft/50" @click="session.logout()"><LogOut class="h-5 w-5" :stroke-width="1.5" />Logout</button>
					</div>
				</aside>
			</div>
		</Transition>
	</Teleport>
</template>
