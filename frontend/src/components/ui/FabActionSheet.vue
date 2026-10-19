<script setup lang="ts">
import { watch } from "vue"

import Spot from "@/components/illustrations/Spot.vue"
import { useNav } from "@/composables/useNav"
import { useUi } from "@/stores/ui"

const ui = useUi()
const { actions } = useNav()
watch(() => ui.fabOpen, (v) => (document.body.style.overflow = v ? "hidden" : ""))
</script>

<template>
	<Teleport to="body">
		<Transition name="fade">
			<div v-if="ui.fabOpen" class="fixed inset-0 z-40 flex items-center justify-center bg-black/40 px-6" @click.self="ui.fabOpen = false" @keydown.esc="ui.fabOpen = false">
				<div class="w-full max-w-[340px] overflow-hidden rounded-xl bg-white shadow-lift" role="dialog" aria-modal="true" aria-label="Quick actions">
					<RouterLink v-for="a in actions" :key="a.to" :to="a.to" class="flex items-center gap-4 border-b border-ink-200 px-4 py-3 last:border-b-0 hover:bg-ink-50" @click="ui.fabOpen = false">
						<span class="grid h-14 w-14 shrink-0 place-items-center overflow-hidden rounded-full bg-ink-100 p-1.5"><Spot :name="a.spot" class="h-full w-full" /></span>
						<span class="text-[15px] text-ink-900">{{ a.label }}</span>
					</RouterLink>
				</div>
			</div>
		</Transition>
	</Teleport>
</template>
