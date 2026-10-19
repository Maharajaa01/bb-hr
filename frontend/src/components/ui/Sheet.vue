<script setup lang="ts">
import { X } from "lucide-vue-next"
import { watch } from "vue"

defineProps<{ title: string }>()
const open = defineModel<boolean>({ required: true })

watch(open, (v) => {
	document.body.style.overflow = v ? "hidden" : ""
})
function onKey(e: KeyboardEvent) {
	if (e.key === "Escape") open.value = false
}
</script>

<template>
	<Teleport to="body">
		<Transition name="fade">
			<div v-if="open" class="fixed inset-0 z-40 flex items-end justify-center bg-ink-950/50 sm:items-center" @click.self="open = false" @keydown="onKey">
				<div class="max-h-[85vh] w-full overflow-y-auto rounded-t-3xl bg-white p-5 shadow-lift safe-bottom sm:max-w-md sm:rounded-3xl" role="dialog" aria-modal="true" :aria-label="title">
					<div class="mb-4 flex items-center justify-between">
						<h2 class="text-lg font-bold">{{ title }}</h2>
						<button class="grid h-9 w-9 place-items-center rounded-xl hover:bg-ink-100" aria-label="Close" @click="open = false"><X class="h-5 w-5" /></button>
					</div>
					<slot />
				</div>
			</div>
		</Transition>
	</Teleport>
</template>
