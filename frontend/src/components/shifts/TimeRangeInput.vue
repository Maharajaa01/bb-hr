<script setup lang="ts">
import { Clock, MoonStar } from "lucide-vue-next"
import { computed } from "vue"

import { duration, isOvernight, periodOf } from "@/lib/shifts"

/** Start / end time pickers with a live summary (period, length, past-midnight note). */
const start = defineModel<string>("start", { required: true })
const end = defineModel<string>("end", { required: true })

const valid = computed(() => !!start.value && !!end.value && start.value !== end.value)
const period = computed(() => periodOf(start.value || "09:00"))
</script>

<template>
	<div>
		<div class="grid grid-cols-2 gap-3">
			<label class="block">
				<span class="label">Start time</span>
				<input v-model="start" type="time" required class="field tabular text-lg font-semibold" />
			</label>
			<label class="block">
				<span class="label">End time</span>
				<input v-model="end" type="time" required class="field tabular text-lg font-semibold" />
			</label>
		</div>
		<div v-if="valid" class="mt-2 flex flex-wrap items-center gap-2 text-[13px]">
			<span class="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-medium" :class="period.chip">
				<component :is="period.icon" class="h-3.5 w-3.5" /> {{ period.label }}
			</span>
			<span class="inline-flex items-center gap-1 text-ink-600"><Clock class="h-3.5 w-3.5" /> {{ duration(start, end) }}</span>
			<span v-if="isOvernight(start, end)" class="inline-flex items-center gap-1 text-indigo-700"><MoonStar class="h-3.5 w-3.5" /> Ends next day</span>
		</div>
		<p v-else-if="start && end" class="mt-2 text-[13px] text-danger">Start and end cannot be the same.</p>
	</div>
</template>
