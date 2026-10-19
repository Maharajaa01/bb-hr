<script setup lang="ts">
import { CalendarCheck, CalendarX, Camera, Clock4, ListFilter, Plane } from "lucide-vue-next"
import { computed, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"

import { call, fileUrl } from "@/api/client"
import type { AttendanceHistory, AttendanceRow } from "@/api/types"
import AttendanceCalendar from "@/components/AttendanceCalendar.vue"
import AppBar from "@/components/ui/AppBar.vue"
import EmptyState from "@/components/ui/EmptyState.vue"
import ErrorState from "@/components/ui/ErrorState.vue"
import HeaderTabs from "@/components/ui/HeaderTabs.vue"
import IconButton from "@/components/ui/IconButton.vue"
import LogTable from "@/components/ui/LogTable.vue"
import Segmented from "@/components/ui/Segmented.vue"
import Skeleton from "@/components/ui/Skeleton.vue"
import StatCard from "@/components/ui/StatCard.vue"
import StatusBadge from "@/components/ui/StatusBadge.vue"
import { useResource } from "@/composables/useResource"
import { clock, formatDate, formatHours, formatTime, isoDate, parseLocal, titleCase } from "@/lib/format"
import { useSession } from "@/stores/session"

const props = defineProps<{ employee?: string }>()
const route = useRoute()
const router = useRouter()
const session = useSession()

const now = new Date()
const pad = (n: number) => String(n).padStart(2, "0")
const q = route.query
const month = ref<string>(q.year && q.month && Number(q.month) > 0 ? `${q.year}-${pad(Number(q.month))}` : `${now.getFullYear()}-${pad(now.getMonth() + 1)}`)
const status = ref<string>(typeof q.status === "string" ? q.status : "")
const view = ref<"calendar" | "list">("calendar")
const showFilter = ref(false)
const selected = ref<string | null>(null)

const range = computed(() => {
	const [y, m] = month.value.split("-").map(Number)
	return { y, m, from: isoDate(new Date(y, m - 1, 1)), to: isoDate(new Date(y, m, 0)) }
})

// one request per month: the calendar needs every day of it
const { data, error, loading, reload } = useResource((signal) =>
	call<AttendanceHistory>("history.get_attendance_history", { employee: props.employee, from_date: range.value.from, to_date: range.value.to, page: 1, page_length: 31 }, { signal }),
)
watch(month, () => {
	selected.value = null
	void reload()
	router.replace({ query: { ...route.query, year: range.value.y, month: range.value.m } })
})

const statuses = computed(() => Object.fromEntries((data.value?.rows ?? []).map((r) => [r.attendance_date, r.status])))
const rows = computed(() => (data.value?.rows ?? []).filter((r) => (!status.value || r.status === status.value) && (!selected.value || r.attendance_date === selected.value)))

function logRows(r: AttendanceRow) {
	const out: { key: string; in: string; out: string; duration: string }[] = []
	let cur: { t: string; ms: number } | null = null
	for (const p of r.punches) {
		const ms = parseLocal(p.time)?.getTime() ?? 0
		if (p.log_type === "IN") cur = { t: p.time, ms }
		else if (cur) {
			out.push({ key: p.name, in: formatTime(cur.t), out: formatTime(p.time), duration: clock((ms - cur.ms) / 1000).replace(/ /g, "") })
			cur = null
		}
	}
	if (cur) out.push({ key: `${r.name}-open`, in: formatTime(cur.t), out: "--:--", duration: "--" })
	if (!out.length && r.in_time) out.push({ key: r.name, in: formatTime(r.in_time), out: formatTime(r.out_time), duration: formatHours(r.working_hours) })
	return out
}

const isSelf = computed(() => !props.employee || props.employee === session.employee?.name)
const title = computed(() => (isSelf.value ? "Attendance" : titleCase(data.value?.employee_name) || "Attendance"))
function photoUrl(checkin: string) {
	return fileUrl("attendance.get_checkin_photo", { checkin })
}
</script>

<template>
	<div>
		<AppBar :title="title" :subtitle="isSelf ? undefined : [titleCase(data?.designation), data?.employee].filter(Boolean).join(' · ')" :back="isSelf ? '/' : '/team'">
			<template v-if="isSelf" #extension><HeaderTabs :tabs="[{ to: '/check-in', label: 'Today' }, { to: '/attendance', label: 'Overview' }]" /></template>
		</AppBar>

		<ErrorState v-if="error" :error="error" :retrying="loading" @retry="reload" />
		<template v-else-if="!data"><div class="flex gap-2.5"><Skeleton v-for="i in 2" :key="i" card :lines="2" class="flex-1" /></div><Skeleton card :lines="7" class="mt-3" /></template>

		<template v-else>
			<div class="no-scrollbar -mx-3 flex gap-2.5 overflow-x-auto px-3 pb-1" :class="loading ? 'opacity-60' : ''">
				<StatCard label="Present Days" :value="data.summary.present" tone="mint" :icon="CalendarCheck" />
				<StatCard label="Working Hours" :value="`${Math.round(data.summary.total_hours)}h`" tone="blue" :icon="Clock4" />
				<StatCard label="Absent" :value="data.summary.absent" tone="lavender" :icon="CalendarX" />
				<StatCard label="On Leave" :value="data.summary.on_leave" tone="peach" :icon="Plane" />
			</div>

			<div class="-mx-3 mt-3 flex items-center justify-between bg-ink-100 px-3 py-1.5">
				<Segmented v-model="view" label="View" :options="[{ value: 'calendar', label: 'Calendar' }, { value: 'list', label: 'List' }]" />
				<IconButton label="Filter by status" :active="showFilter || !!status" @click="showFilter = !showFilter"><ListFilter class="h-5 w-5" /></IconButton>
			</div>
			<div v-if="showFilter" class="no-scrollbar -mx-3 mt-2 flex gap-2 overflow-x-auto px-3">
				<button v-for="s in ['', 'Present', 'Absent', 'Half Day', 'On Leave']" :key="s" class="h-9 shrink-0 rounded-full border px-3 text-[13px]" :class="status === s ? 'border-brand-500 bg-brand-500 text-white' : 'border-ink-200 bg-white text-ink-700'" :aria-pressed="status === s" @click="status = s">{{ s || "All" }}</button>
			</div>

			<h2 class="section-title mb-2 mt-4">Monthly Attendance</h2>
			<AttendanceCalendar v-if="view === 'calendar'" v-model:month="month" v-model:selected="selected" :statuses="statuses" :loading="loading" legend />

			<section class="mt-3 space-y-2.5">
				<p v-if="view === 'calendar' && !selected" class="text-center text-[13px] text-ink-500">Tap a day to see its punches</p>
				<template v-if="view === 'list' || selected">
					<article v-for="r in rows" :key="r.name" class="card overflow-hidden">
						<div class="flex items-center justify-between gap-2 px-3.5 py-2.5">
							<p class="font-medium">{{ formatDate(r.attendance_date, { weekday: true }) }}</p>
							<div class="flex items-center gap-1.5">
								<StatusBadge v-if="r.late_entry" status="Late" /><StatusBadge :status="r.status" />
								<template v-if="!isSelf"><a v-for="p in r.punches.filter((x) => x.has_photo)" :key="p.name" :href="photoUrl(p.name)" target="_blank" rel="noopener" class="grid h-8 w-8 place-items-center rounded-full text-ink-500 hover:bg-ink-50" :aria-label="`Photo for ${formatTime(p.time)} punch`"><Camera class="h-4 w-4" /></a></template>
							</div>
						</div>
						<LogTable v-if="r.status !== 'On Leave' && r.status !== 'Absent'" :rows="logRows(r)" empty="No punches recorded" />
						<p v-else class="border-t border-ink-200 px-3.5 py-2.5 text-[13px] text-ink-500">{{ r.leave_type || r.status }}</p>
					</article>
					<div v-if="!rows.length" class="card"><EmptyState :description="selected ? `Nothing recorded on ${formatDate(selected)}.` : 'No attendance recorded for this month.'" /></div>
				</template>
			</section>
		</template>
	</div>
</template>
