<script setup lang="ts">
import { ChevronLeft, ChevronRight } from "lucide-vue-next"
import { computed } from "vue"

import { formatDate, isoDate, MONTH_NAMES } from "@/lib/format"

/** Month grid with tinted day tiles: present green, absent red, leave orange, half day split. */
const props = defineProps<{ statuses: Record<string, string>; loading?: boolean; legend?: boolean }>()
const month = defineModel<string>("month", { required: true }) // "YYYY-MM"
const selected = defineModel<string | null>("selected", { default: null })

const todayIso = isoDate(new Date())
const parts = computed(() => month.value.split("-").map(Number))
const title = computed(() => `${MONTH_NAMES[parts.value[1] - 1]} ${parts.value[0]}`)

const cells = computed(() => {
	const [y, m] = parts.value
	const lead = new Date(y, m - 1, 1).getDay()
	const days = new Date(y, m, 0).getDate()
	const out: ({ date: string; day: number } | null)[] = Array(lead).fill(null)
	for (let d = 1; d <= days; d++) out.push({ date: isoDate(new Date(y, m - 1, d)), day: d })
	return out
})

function shift(delta: number) {
	const [y, m] = parts.value
	const d = new Date(y, m - 1 + delta, 1)
	month.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`
	selected.value = null
}

function tone(date: string) {
	const s = props.statuses[date]
	switch (s) {
		case "Present":
		case "Work From Home":
			return "bg-success-soft text-ink-900"
		case "Absent":
			return "bg-danger-soft text-ink-900"
		case "On Leave":
			return "bg-warning-soft text-ink-900"
		case "Half Day":
			return "bg-gradient-to-br from-success-soft from-50% to-white to-50% text-ink-900 ring-1 ring-inset ring-success-soft"
		default:
			return "text-ink-900"
	}
}
</script>

<template>
	<section class="card p-3" :class="loading ? 'opacity-60' : ''">
		<div class="mb-2 flex items-center justify-between">
			<button class="grid h-11 w-11 place-items-center rounded-full hover:bg-ink-50" aria-label="Previous month" @click="shift(-1)"><ChevronLeft class="h-5 w-5" /></button>
			<h3 class="text-[18px] font-semibold" aria-live="polite">{{ title }}</h3>
			<button class="grid h-11 w-11 place-items-center rounded-full hover:bg-ink-50" aria-label="Next month" @click="shift(1)"><ChevronRight class="h-5 w-5" /></button>
		</div>
		<div class="grid grid-cols-7 text-center text-[13px] text-ink-700">
			<span v-for="d in ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']" :key="d" aria-hidden="true">{{ d }}</span>
		</div>
		<div class="mt-2 grid grid-cols-7 gap-1.5">
			<template v-for="(c, i) in cells" :key="i">
				<div v-if="!c" />
				<button
					v-else
					class="mx-auto grid h-10 w-10 place-items-center rounded-lg text-[15px] transition"
					:class="[
						selected === c.date ? '!bg-brand-500 !text-white' : tone(c.date),
						c.date === todayIso && selected !== c.date ? '!text-brand-500 font-semibold' : '',
						c.date > todayIso ? 'opacity-40' : '',
					]"
					:aria-label="`${formatDate(c.date)}${statuses[c.date] ? ': ' + statuses[c.date] : ''}`"
					:aria-pressed="selected === c.date"
					@click="selected = selected === c.date ? null : c.date"
				>
					{{ c.day }}
				</button>
			</template>
		</div>
		<div v-if="legend" class="mt-3 flex flex-wrap justify-center gap-x-4 gap-y-1 text-[12px] text-ink-600">
			<span class="inline-flex items-center gap-1.5"><span class="h-3 w-3 rounded bg-success-soft ring-1 ring-success/30" />Present</span>
			<span class="inline-flex items-center gap-1.5"><span class="h-3 w-3 rounded bg-danger-soft ring-1 ring-danger/30" />Absent</span>
			<span class="inline-flex items-center gap-1.5"><span class="h-3 w-3 rounded bg-warning-soft ring-1 ring-warning/40" />Leave</span>
			<span class="inline-flex items-center gap-1.5"><span class="h-3 w-3 rounded bg-gradient-to-br from-success-soft from-50% to-white to-50% ring-1 ring-success/30" />Half day</span>
		</div>
	</section>
</template>
