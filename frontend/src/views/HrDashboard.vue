<script setup lang="ts">
import { AlertTriangle, CalendarCheck, CalendarX, ChevronRight, Clock4, MapPin, Plane, Settings2, UserCheck, Users, UserX } from "lucide-vue-next"
import { computed, ref } from "vue"

import { call } from "@/api/client"
import type { HrOverview } from "@/api/types"
import ErrorState from "@/components/ui/ErrorState.vue"
import AppBar from "@/components/ui/AppBar.vue"
import Skeleton from "@/components/ui/Skeleton.vue"
import StatTile from "@/components/ui/StatTile.vue"
import { useResource } from "@/composables/useResource"
import { formatDate, weekday } from "@/lib/format"
import { useSession } from "@/stores/session"

const session = useSession()
const { data, error, loading, reload } = useResource((signal) => call<HrOverview>("team.get_hr_overview", {}, { signal }))

const maxTrend = computed(() => Math.max(1, ...(data.value?.trend ?? []).map((t) => t.present)))
const hovered = ref<number | null>(null)
const showTable = ref(false)

const setupIssues = computed(() => {
	const s = data.value?.setup
	if (!s) return []
	const out: { text: string; href: string }[] = []
	if (s.geofence && !s.office_locations) out.push({ text: "No office location configured - every check-in will be refused.", href: "/app/bb-hr-settings" })
	if (s.employees_without_user) out.push({ text: `${s.employees_without_user} active employees have no login linked, so they cannot use BB HRMS.`, href: "/app/employee?status=Active&user_id=%5B%22is%22%2C%22not%20set%22%5D" })
	if (s.employees_without_manager) out.push({ text: `${s.employees_without_manager} active employees have no Reports To, so no manager sees them.`, href: "/app/employee?status=Active&reports_to=%5B%22is%22%2C%22not%20set%22%5D" })
	return out
})
</script>

<template>
	<div>
		<AppBar title="HR dashboard" :subtitle="data ? formatDate(data.date, { weekday: true }) : undefined">
			<template #actions>
				<a v-if="session.info?.desk_access" href="/app/bb-hr-settings" class="grid h-11 w-11 place-items-center rounded-full hover:bg-white/15" aria-label="BB HR Settings"><Settings2 class="h-5 w-5" /></a>
			</template>
		</AppBar>

		<ErrorState v-if="error" :error="error" :retrying="loading" @retry="reload" />
		<template v-else-if="!data">
			<div class="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4"><Skeleton v-for="i in 8" :key="i" card :lines="2" /></div>
		</template>
		<div v-else class="space-y-6">
			<div v-if="setupIssues.length" class="space-y-2">
				<a v-for="i in setupIssues" :key="i.text" :href="session.info?.desk_access ? i.href : undefined" class="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-3.5 text-sm text-amber-900">
					<AlertTriangle class="mt-0.5 h-4 w-4 shrink-0" /> <span class="flex-1">{{ i.text }}</span>
				</a>
			</div>

			<section>
				<h2 class="section-title mb-3">Today</h2>
				<div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
					<StatTile label="Headcount" :value="data.summary.total" :icon="Users" />
					<StatTile label="Present" :value="data.summary.present + data.summary.half_day" :hint="data.summary.total ? `${Math.round(((data.summary.present + data.summary.half_day) / data.summary.total) * 100)}% of staff` : undefined" :icon="CalendarCheck" tone="success" />
					<StatTile label="In now" :value="data.summary.currently_in" :icon="UserCheck" tone="success" />
					<StatTile label="Late" :value="data.summary.late" :icon="Clock4" tone="warning" />
					<StatTile label="On leave" :value="data.summary.on_leave" :icon="Plane" tone="info" />
					<StatTile label="Holiday / off" :value="data.summary.holiday" :icon="CalendarX" tone="gold" />
					<StatTile label="Not marked" :value="data.summary.not_marked" :icon="UserX" tone="danger" />
					<StatTile label="Office locations" :value="data.setup.office_locations" :hint="data.setup.geofence ? 'Geofence on' : 'Geofence off'" :icon="MapPin" />
				</div>
			</section>

			<div class="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
				<section class="card p-5">
					<div class="mb-1 flex items-baseline justify-between">
						<h2 class="section-title">Present per day</h2>
						<button class="text-sm font-medium text-ink-500 hover:text-ink-800" @click="showTable = !showTable">{{ showTable ? "Chart" : "Table" }}</button>
					</div>
					<p class="mb-4 text-xs text-ink-500">Last 14 days, submitted attendance</p>
					<p v-if="!showTable && !data.trend.some((t) => t.present || t.absent || t.on_leave)" class="grid h-40 place-items-center rounded-xl bg-ink-50 px-4 text-center text-sm text-ink-500">No submitted attendance in the last 14 days.</p>
					<div v-else-if="!showTable" class="relative">
						<div class="flex h-40 items-end gap-[2px] border-b border-ink-200" role="img" :aria-label="`Present per day, last 14 days. Peak ${maxTrend}.`">
							<div
								v-for="(t, i) in data.trend"
								:key="t.date"
								class="group relative flex h-full flex-1 items-end"
								@mouseenter="hovered = i"
								@mouseleave="hovered = null"
								@focus="hovered = i"
								@blur="hovered = null"
								tabindex="0"
							>
								<div class="w-full rounded-t-[4px] transition-colors" :class="hovered === i ? 'bg-brand-700' : 'bg-brand-500'" :style="{ height: `${(t.present / maxTrend) * 100}%`, minHeight: t.present ? '4px' : '0' }" />
								<div v-if="hovered === i" class="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 w-max -translate-x-1/2 rounded-xl bg-brand-800 px-3 py-2 text-xs text-white shadow-lift">
									<p class="font-semibold">{{ formatDate(t.date, { weekday: true, year: false }) }}</p>
									<p>Present {{ t.present }} · Absent {{ t.absent }} · Leave {{ t.on_leave }}</p>
								</div>
							</div>
						</div>
						<div class="mt-1.5 flex gap-[2px] text-center text-[10px] text-ink-400">
							<span v-for="(t, i) in data.trend" :key="t.date" class="flex-1">{{ i % 2 === 0 ? weekday(t.date)[0] + t.date.slice(8) : "" }}</span>
						</div>
					</div>
					<table v-else class="w-full text-sm">
						<thead><tr class="text-left text-ink-500"><th class="py-1 font-medium">Date</th><th class="text-right font-medium">Present</th><th class="text-right font-medium">Absent</th><th class="text-right font-medium">Leave</th></tr></thead>
						<tbody class="tabular">
							<tr v-for="t in data.trend" :key="t.date" class="border-t border-ink-100"><td class="py-1.5">{{ formatDate(t.date, { weekday: true, year: false }) }}</td><td class="text-right">{{ t.present }}</td><td class="text-right">{{ t.absent }}</td><td class="text-right">{{ t.on_leave }}</td></tr>
						</tbody>
					</table>
				</section>

				<section class="card p-5">
					<h2 class="section-title mb-4">By department today</h2>
					<ul class="space-y-3">
						<li v-for="d in data.departments" :key="d.department">
							<div class="mb-1 flex justify-between gap-2 text-sm"><span class="truncate font-medium">{{ d.department.replace(/ - BBA$/, "") }}</span><span class="tabular shrink-0 text-ink-500">{{ d.present }} / {{ d.total }}</span></div>
							<div class="h-2 rounded-full bg-brand-50"><div class="h-2 rounded-full bg-brand-500" :style="{ width: `${(d.present / Math.max(d.total, 1)) * 100}%` }" /></div>
						</li>
					</ul>
				</section>
			</div>

			<section class="grid gap-3 sm:grid-cols-3">
				<RouterLink v-for="l in [{ to: '/team', t: 'Company attendance', d: 'Who is in, by person' }, { to: '/exceptions', t: 'Exceptions', d: 'Late, missing check-outs, unmarked' }, { to: '/directory', t: 'Directory', d: 'Employees, contacts, payslips' }]" :key="l.to" :to="l.to" class="card flex items-center gap-3 p-4 hover:border-brand-300">
					<span class="flex-1"><span class="block font-semibold">{{ l.t }}</span><span class="text-sm text-ink-500">{{ l.d }}</span></span>
					<ChevronRight class="h-5 w-5 text-ink-300" />
				</RouterLink>
			</section>
		</div>
	</div>
</template>
