<script setup lang="ts">
import { AlertTriangle, CalendarCheck, CalendarX, ChevronRight, Clock4, Plane, Search, UserCheck, Users } from "lucide-vue-next"
import { computed, ref, watch } from "vue"

import { call } from "@/api/client"
import type { TeamOverview } from "@/api/types"
import Avatar from "@/components/ui/Avatar.vue"
import EmptyState from "@/components/ui/EmptyState.vue"
import ErrorState from "@/components/ui/ErrorState.vue"
import AppBar from "@/components/ui/AppBar.vue"
import Skeleton from "@/components/ui/Skeleton.vue"
import StatTile from "@/components/ui/StatTile.vue"
import StatusBadge from "@/components/ui/StatusBadge.vue"
import { useResource } from "@/composables/useResource"
import { formatDate, formatTime, isoDate, titleCase } from "@/lib/format"
import { useSession } from "@/stores/session"

const session = useSession()
const todayIso = isoDate(new Date())
const date = ref(todayIso)
const department = ref("")
const filter = ref("")
const search = ref("")

const departments = useResource((signal) => call<string[]>("team.get_departments", {}, { signal }))
const { data, error, loading, reload } = useResource((signal) =>
	call<TeamOverview>("team.get_team_overview", { date: date.value, department: department.value }, { signal }),
)
watch([date, department], () => reload())

const rows = computed(() => {
	const q = search.value.trim().toLowerCase()
	return (data.value?.rows ?? []).filter((r) => {
		if (q && !(r.employee_name || "").toLowerCase().includes(q) && !r.employee.toLowerCase().includes(q)) return false
		if (!filter.value) return true
		if (filter.value === "In Now") return r.currently_in
		if (filter.value === "Late") return r.late_minutes > 0
		if (filter.value === "Present") return ["Present", "Work From Home", "Half Day"].includes(r.status)
		return r.status === filter.value
	})
})

function toggle(f: string) {
	filter.value = filter.value === f ? "" : f
}
</script>

<template>
	<div>
		<AppBar :title="data?.scope === 'company' ? 'Company attendance' : 'Team attendance'" :subtitle="data ? `${formatDate(data.date, { weekday: true })} · ${data.summary.total} employees` : undefined">
		</AppBar>

		<ErrorState v-if="error && !data" :error="error" :retrying="loading" @retry="reload" />
		<template v-else-if="!data">
			<div class="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-5"><Skeleton v-for="i in 5" :key="i" card :lines="2" /></div>
			<Skeleton card :lines="8" />
		</template>
		<template v-else>
			<div class="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6" :class="loading ? 'opacity-60' : ''">
				<StatTile clickable :active="filter === 'Present'" label="Present" :value="data.summary.present + data.summary.half_day" :icon="CalendarCheck" tone="success" @click="toggle('Present')" />
				<StatTile v-if="date === todayIso" clickable :active="filter === 'In Now'" label="In now" :value="data.summary.currently_in" :icon="UserCheck" tone="success" @click="toggle('In Now')" />
				<StatTile clickable :active="filter === 'Late'" label="Late" :value="data.summary.late" :icon="Clock4" tone="warning" @click="toggle('Late')" />
				<StatTile clickable :active="filter === 'On Leave'" label="On leave" :value="data.summary.on_leave" :icon="Plane" tone="info" @click="toggle('On Leave')" />
				<StatTile clickable :active="filter === 'Not Marked'" label="Not marked" :value="data.summary.not_marked" :icon="AlertTriangle" tone="danger" @click="toggle('Not Marked')" />
				<StatTile clickable :active="filter === 'Absent'" label="Absent" :value="data.summary.absent" :icon="CalendarX" tone="danger" @click="toggle('Absent')" />
			</div>

			<div class="mb-3 flex flex-col gap-2 sm:flex-row">
				<label class="sm:w-44"><span class="sr-only">Date</span><input v-model="date" type="date" class="field" :max="todayIso" /></label>
				<label class="relative flex-1"><span class="sr-only">Search</span>
					<Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" />
					<input v-model="search" type="search" class="field pl-9" placeholder="Search by name or ID" />
				</label>
				<label v-if="session.isHr && departments.data.value?.length" class="sm:w-64"><span class="sr-only">Department</span>
					<select v-model="department" class="field"><option value="">All departments</option><option v-for="d in departments.data.value" :key="d" :value="d">{{ d }}</option></select>
				</label>
			</div>

			<div class="card divide-y divide-brand-50" :class="loading ? 'opacity-60' : ''">
				<RouterLink v-for="r in rows" :key="r.employee" :to="`/team/${r.employee}`" class="flex items-center gap-3 px-4 py-3 hover:bg-brand-50/60">
					<div class="relative"><Avatar :name="r.employee_name" :image="r.image" /><span v-if="r.currently_in" class="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-emerald-500 ring-2 ring-white" aria-label="Checked in now" /></div>
					<div class="min-w-0 flex-1">
						<p class="truncate font-semibold">{{ titleCase(r.employee_name) }}</p>
						<p class="truncate text-sm text-ink-500">
							<template v-if="r.first_in">In {{ formatTime(r.first_in) }}<template v-if="r.last_out"> · Out {{ formatTime(r.last_out) }}</template><template v-if="r.location"> · {{ r.location }}</template></template>
							<template v-else-if="r.holiday !== null">Off today<template v-if="r.holiday && !/^(Sun|Mon|Tues|Wednes|Thurs|Fri|Satur)day$/.test(r.holiday)"> · {{ r.holiday }}</template></template>
							<template v-else>{{ titleCase(r.designation) || r.employee }}</template>
						</p>
					</div>
					<div class="flex shrink-0 flex-col items-end gap-1">
						<StatusBadge :status="r.status" />
						<span v-if="r.late_minutes > 0" class="text-xs font-medium text-amber-700">{{ r.late_minutes }} min late</span>
					</div>
					<ChevronRight class="h-5 w-5 shrink-0 text-ink-300" />
				</RouterLink>
				<EmptyState v-if="!rows.length" :icon="Users" :title="data.rows.length ? 'No one matches' : 'No team members'" :description="data.rows.length ? 'Try a different filter or search.' : 'Employees who report to you appear here once HR sets Reports To on their records.'" />
			</div>
		</template>
	</div>
</template>
