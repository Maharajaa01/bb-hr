<script setup lang="ts">
import { ChevronDown } from "lucide-vue-next"
import { computed } from "vue"

import { MONTH_NAMES } from "@/lib/format"

/** Month picker pill (left) + icon buttons slot (right). v-model is "YYYY-MM". */
const model = defineModel<string>({ required: true })
const label = computed(() => {
	const [y, m] = model.value.split("-").map(Number)
	return `${MONTH_NAMES[m - 1].slice(0, 3)}, ${y}`
})
</script>

<template>
	<div class="mb-3 flex items-center justify-between gap-2">
		<label class="relative inline-flex h-10 items-center gap-1.5 rounded-[10px] border border-ink-200 bg-white px-3 text-[14px]">
			<span>{{ label }}</span><ChevronDown class="h-4 w-4 text-ink-500" />
			<input v-model="model" type="month" class="absolute inset-0 cursor-pointer opacity-0" aria-label="Month" />
		</label>
		<div class="flex items-center gap-2"><slot /></div>
	</div>
</template>
