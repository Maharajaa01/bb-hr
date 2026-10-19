<script setup lang="ts">
import { ChevronLeft, ChevronRight } from "lucide-vue-next"
import { computed, ref, watch } from "vue"

import { call } from "@/api/client"
import type { Holiday, HolidayCalendar } from "@/api/types"
import AppBar from "@/components/ui/AppBar.vue"
import EmptyState from "@/components/ui/EmptyState.vue"
import ErrorState from "@/components/ui/ErrorState.vue"
import IconButton from "@/components/ui/IconButton.vue"
import Skeleton from "@/components/ui/Skeleton.vue"
import { useResource } from "@/composables/useResource"
import { isoDate, MONTH_NAMES, parseLocal } from "@/lib/format"

const todayIso = isoDate(new Date())
const year = ref(new Date().getFullYear())
const showWeeklyOff = ref(false)

const { data, error, loading, reload } = useResource((signal) => call<HolidayCalendar>("holidays.get_holidays", { year: year.value }, { signal }))
watch(year, () => reload())

const FULL_DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
const groups = computed(() => {
	const out = new Map<number, Holiday[]>()
	for (const h of data.value?.holidays ?? []) {
		if (h.weekly_off && !showWeeklyOff.value) continue
		const m = parseLocal(h.date)!.getMonth()
		out.set(m, [...(out.get(m) ?? []), h])
	}
	return [...out.entries()].map(([m, list]) => ({ month: MONTH_NAMES[m], list }))
})
const publicCount = computed(() => (data.value?.holidays ?? []).filter((h) => !h.weekly_off).length)
function day(h: Holiday) {
	return FULL_DAYS[parseLocal(h.date)!.getDay()]
}
</script>

<template>
	<div>
		<AppBar title="Holiday List" :subtitle="data?.holiday_list ? `${data.holiday_list} · ${publicCount} holidays` : undefined" back="/" />

		<div class="mb-3 flex items-center justify-between">
			<div class="flex items-center gap-2">
				<IconButton label="Previous year" @click="year--"><ChevronLeft class="h-5 w-5" /></IconButton>
				<span class="tabular w-12 text-center text-[16px] font-medium">{{ year }}</span>
				<IconButton label="Next year" @click="year++"><ChevronRight class="h-5 w-5" /></IconButton>
			</div>
			<label class="inline-flex h-11 items-center gap-2 text-[14px] text-ink-700"><input v-model="showWeeklyOff" type="checkbox" class="h-4 w-4 rounded border-ink-300 accent-brand-500" />Weekly offs</label>
		</div>

		<ErrorState v-if="error" :error="error" :retrying="loading" @retry="reload" />
		<div v-else-if="!data" class="space-y-2.5"><Skeleton v-for="i in 4" :key="i" card :lines="2" /></div>
		<div v-else-if="!data.holiday_list" class="card"><EmptyState spot="holiday" title="No holiday list assigned" description="Ask HR to set a holiday list on your employee record or the company." /></div>
		<div v-else :class="loading ? 'opacity-60' : ''">
			<section v-for="g in groups" :key="g.month" class="mb-4">
				<h2 class="mb-2 text-[15px] font-medium text-ink-700">{{ g.month }}</h2>
				<div class="space-y-2">
					<article v-for="h in g.list" :key="h.date" class="card flex items-center gap-3 p-2.5" :class="h.date < todayIso ? 'opacity-50' : ''">
						<div class="grid h-14 w-14 shrink-0 place-items-center rounded-lg text-center leading-none" :class="h.weekly_off ? 'bg-ink-100' : 'bg-brand-50'">
							<span class="text-xl font-semibold" :class="h.weekly_off ? 'text-ink-600' : 'text-brand-600'">{{ h.date.slice(8) }}</span>
							<span class="text-[11px] uppercase text-ink-500">{{ day(h).slice(0, 3) }}</span>
						</div>
						<div class="min-w-0"><p class="truncate font-medium">{{ h.weekly_off ? "Weekly off" : h.description }}</p><p class="text-[13px] text-ink-500">{{ day(h) }}</p></div>
					</article>
				</div>
			</section>
			<div v-if="!groups.length" class="card"><EmptyState spot="holiday" :title="`No holidays in ${year}`" /></div>
		</div>
	</div>
</template>
