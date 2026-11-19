<script setup lang="ts">
import { computed } from "vue"

import { periodOf, timeRange } from "@/lib/shifts"

/** A coloured pill for one shift: period icon + time range, optional second line. */
const props = defineProps<{ start: string; end: string; sub?: string; clickable?: boolean; selected?: boolean }>()
const period = computed(() => periodOf(props.start))
</script>

<template>
	<component
		:is="clickable ? 'button' : 'span'"
		:type="clickable ? 'button' : undefined"
		class="inline-flex max-w-full items-center gap-1.5 rounded-xl border px-2.5 py-1.5 text-left transition"
		:class="[period.chip, clickable ? 'hover:brightness-95 active:scale-[.98]' : '', selected ? 'ring-2 ring-brand-500 ring-offset-1' : '']"
	>
		<component :is="period.icon" class="h-4 w-4 shrink-0" aria-hidden="true" />
		<span class="min-w-0">
			<span class="tabular block whitespace-nowrap text-[13px] font-semibold leading-tight">{{ timeRange(start, end) }}</span>
			<span v-if="sub" class="block truncate text-[11px] leading-tight opacity-80">{{ sub }}</span>
		</span>
	</component>
</template>
