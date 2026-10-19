<script setup lang="ts">
import { AlertTriangle, CheckCircle2 } from "lucide-vue-next"
import { computed, ref, watch } from "vue"

import { call } from "@/api/client"
import type { ExceptionReport } from "@/api/types"
import EmptyState from "@/components/ui/EmptyState.vue"
import ErrorState from "@/components/ui/ErrorState.vue"
import AppBar from "@/components/ui/AppBar.vue"
import Skeleton from "@/components/ui/Skeleton.vue"
import StatusBadge from "@/components/ui/StatusBadge.vue"
import { useResource } from "@/composables/useResource"
import { formatDate, formatTime, isoDate, titleCase } from "@/lib/format"

const KINDS = ["Late Arrival", "Missing Check-out", "Not Marked", "Absent"] as const
const today = new Date()
const toDate = ref(isoDate(today))
const fromDate = ref(isoDate(new Date(today.getFullYear(), today.getMonth(), today.getDate() - 6)))
const kind = ref("")

const { data, error, loading, reload } = useResource((signal) => call<ExceptionReport>("team.get_exceptions", { from_date: fromDate.value, to_date: toDate.value }, { signal }))
watch([fromDate, toDate], () => reload())

const rows = computed(() => (data.value?.rows ?? []).filter((r) => !kind.value || r.kind === kind.value))

function preset(days: number) {
	const t = new Date()
	toDate.value = isoDate(t)
	fromDate.value = isoDate(new Date(t.getFullYear(), t.getMonth(), t.getDate() - (days - 1)))
}
</script>

<template>
	<div>
		<AppBar title="Attendance exceptions" subtitle="Late arrivals, missing check-outs and unmarked working days" />

		<div class="mb-3 flex flex-wrap items-end gap-2">
			<label><span class="label">From</span><input v-model="fromDate" type="date" class="field !py-2" :max="toDate" /></label>
			<label><span class="label">To</span><input v-model="toDate" type="date" class="field !py-2" :min="fromDate" :max="isoDate(today)" /></label>
			<div class="flex gap-1">
				<button class="rounded-lg px-3 py-2 text-sm font-medium text-ink-600 hover:bg-ink-100" @click="preset(1)">Today</button>
				<button class="rounded-lg px-3 py-2 text-sm font-medium text-ink-600 hover:bg-ink-100" @click="preset(7)">7 days</button>
				<button class="rounded-lg px-3 py-2 text-sm font-medium text-ink-600 hover:bg-ink-100" @click="preset(30)">30 days</button>
			</div>
		</div>

		<div class="mb-4 flex flex-wrap gap-2" role="group" aria-label="Filter by type">
			<button class="rounded-full border px-3 py-1.5 text-sm font-medium" :class="!kind ? 'border-brand-600 bg-brand-600 text-white' : 'border-ink-200 bg-white text-ink-700'" :aria-pressed="!kind" @click="kind = ''">All · {{ data?.rows.length ?? 0 }}</button>
			<button
				v-for="k in KINDS"
				:key="k"
				class="rounded-full border px-3 py-1.5 text-sm font-medium"
				:class="kind === k ? 'border-brand-600 bg-brand-600 text-white' : 'border-ink-200 bg-white text-ink-700'"
				:aria-pressed="kind === k"
				@click="kind = kind === k ? '' : k"
			>
				{{ k }} · {{ data?.counts[k] ?? 0 }}
			</button>
		</div>

		<ErrorState v-if="error" :error="error" :retrying="loading" @retry="reload" />
		<Skeleton v-else-if="!data" card :lines="8" />
		<div v-else class="card divide-y divide-brand-50" :class="loading ? 'opacity-60' : ''">
			<RouterLink v-for="(r, i) in rows" :key="i" :to="`/team/${r.employee}?year=${r.date.slice(0, 4)}&month=${+r.date.slice(5, 7)}`" class="flex items-center gap-3 px-4 py-3 hover:bg-brand-50/60">
				<span class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-amber-50 text-amber-600"><AlertTriangle class="h-5 w-5" /></span>
				<div class="min-w-0 flex-1">
					<p class="truncate font-semibold">{{ titleCase(r.employee_name) }}</p>
					<p class="truncate text-sm text-ink-500">{{ formatDate(r.date, { weekday: true }) }} · {{ r.detail }}<template v-if="r.time"> ({{ formatTime(r.time) }})</template></p>
				</div>
				<StatusBadge :status="r.kind" />
			</RouterLink>
			<EmptyState v-if="!rows.length" :icon="CheckCircle2" title="No exceptions" description="Everyone in scope punched on time and checked out in this period." />
			<p v-if="data.truncated" class="px-4 py-3 text-sm text-ink-500">Showing the first 500. Narrow the date range to see the rest.</p>
		</div>
	</div>
</template>
