<script setup lang="ts">
import { Briefcase, CalendarCheck, CalendarDays, CalendarX, MoreHorizontal, Timer } from "lucide-vue-next"
import { computed, ref, watch } from "vue"

import { call } from "@/api/client"
import type { AttendanceHistory, Dashboard } from "@/api/types"
import AttendanceCalendar from "@/components/AttendanceCalendar.vue"
import HandPhone from "@/components/illustrations/HandPhone.vue"
import Skyline from "@/components/illustrations/Skyline.vue"
import AppBar from "@/components/ui/AppBar.vue"
import Avatar from "@/components/ui/Avatar.vue"
import EmptyState from "@/components/ui/EmptyState.vue"
import ErrorState from "@/components/ui/ErrorState.vue"
import QuickLinkTile from "@/components/ui/QuickLinkTile.vue"
import Skeleton from "@/components/ui/Skeleton.vue"
import StatCard from "@/components/ui/StatCard.vue"
import MaskedAmount from "@/components/ui/MaskedAmount.vue"
import { useNav } from "@/composables/useNav"
import { useResource } from "@/composables/useResource"
import { formatDate, formatMoney, isoDate, monthLabel, ordinalDate, titleCase } from "@/lib/format"
import { useSession } from "@/stores/session"
import { useUi } from "@/stores/ui"

const session = useSession()
const ui = useUi()
const { items } = useNav()
const { data, error, loading, reload } = useResource((signal) => call<Dashboard>("dashboard.get_dashboard", {}, { signal }))

const now = new Date()
const month = ref(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`)
const selectedDay = ref<string | null>(null)
const att = useResource((signal) => {
	const [y, m] = month.value.split("-").map(Number)
	return call<AttendanceHistory>("history.get_attendance_history", { from_date: isoDate(new Date(y, m - 1, 1)), to_date: isoDate(new Date(y, m, 0)), page_length: 31 }, { signal })
})
watch(month, () => att.reload())
const statuses = computed(() => Object.fromEntries((att.data.value?.rows ?? []).map((r) => [r.attendance_date, r.status])))

const tiles = computed(() => items.value.filter((i) => i.to !== "/" && i.to !== "/profile"))
const checkedIn = computed(() => !!data.value?.today.checked_in)
</script>

<template>
	<div>
		<AppBar title="Dashboard" />

		<!-- hero + overlapping profile card -->
		<div class="-mx-3 -mt-3 h-[180px] overflow-hidden"><Skyline /></div>
		<section class="relative -mt-10 overflow-hidden rounded-xl border border-ink-200 bg-gradient-to-br from-white to-lavender shadow-card">
			<div class="flex items-center gap-3 p-3.5">
				<Avatar :name="session.displayName" :image="session.employee?.image" size="lg" />
				<div class="min-w-0 flex-1">
					<p class="truncate text-base font-medium">{{ titleCase(session.displayName) }}</p>
					<p class="flex items-center gap-1 truncate text-[13px] text-ink-500"><Briefcase class="h-3.5 w-3.5 shrink-0" />{{ titleCase(session.employee?.designation) || "Employee" }}</p>
				</div>
				<p class="shrink-0 self-start text-[13px] text-ink-500">{{ ordinalDate(new Date()) }}</p>
			</div>
			<RouterLink
				to="/check-in"
				class="relative flex h-12 items-center justify-center gap-2 text-[15px] font-medium text-white"
				:class="checkedIn ? 'bg-gradient-to-r from-[#E8456B] to-danger' : 'bg-gradient-to-r from-brand-400 to-brand-600'"
			>
				<HandPhone class="absolute -bottom-1 left-2 h-12 w-11" />
				<Timer class="h-5 w-5" />{{ checkedIn ? "Click To Check Out" : "Click To Check In" }}
			</RouterLink>
		</section>

		<ErrorState v-if="error && !data" class="mt-4" :error="error" :retrying="loading" @retry="reload" />

		<!-- quick links -->
		<section class="mt-6">
			<div class="mb-3 flex items-center justify-between">
				<h2 class="section-title">Quick Links</h2>
				<button class="grid h-11 w-11 place-items-center rounded-full text-ink-500 hover:bg-ink-50" aria-label="All pages" @click="ui.drawerOpen = true"><MoreHorizontal class="h-5 w-5" /></button>
			</div>
			<div class="grid grid-cols-3 gap-2.5">
				<QuickLinkTile v-for="t in tiles" :key="t.to" :to="t.to" :label="t.label" :spot="t.spot" />
			</div>
		</section>

		<template v-if="!data && !error">
			<div class="mt-6 flex gap-2.5"><Skeleton v-for="i in 3" :key="i" card :lines="2" class="flex-1" /></div>
			<Skeleton card :lines="4" class="mt-6" />
		</template>

		<template v-if="data">
			<!-- leave balance -->
			<section class="mt-6">
				<h2 class="section-title mb-3">Leave Balance</h2>
				<div class="no-scrollbar -mx-3 flex gap-2.5 overflow-x-auto px-3 pb-1">
					<StatCard label="Total" :value="data.leave_balance.total" tone="lavender" :icon="CalendarDays" />
					<StatCard label="Used" :value="data.leave_balance.used" tone="peach" :icon="CalendarX" />
					<StatCard label="Available" :value="data.leave_balance.available" tone="mint" :icon="CalendarCheck" />
				</div>
			</section>

			<!-- salary slips -->
			<section class="mt-6">
				<div class="mb-3 flex items-baseline justify-between">
					<h2 class="section-title">Salary Slip</h2>
					<RouterLink to="/salary" class="text-[13px] text-ink-500 hover:text-brand-500">Show More</RouterLink>
				</div>
				<div class="space-y-2.5">
					<RouterLink v-for="s in data.recent_slips" :key="s.name" :to="`/salary/${encodeURIComponent(s.name)}`" class="card block p-3.5">
						<div class="flex items-center justify-between">
							<p class="text-[15px]">{{ monthLabel(s.start_date).split(" ")[0] }} • {{ formatDate(s.posting_date, { year: false }) }}</p>
							<span class="inline-flex items-center gap-1 text-[14px] font-medium text-success">Submitted<span class="h-2 w-2 rounded-full bg-success" /></span>
						</div>
						<div class="mt-2 flex items-center justify-between">
							<p class="truncate text-[14px] text-ink-700">{{ s.name }}</p>
							<MaskedAmount :amount="s.rounded_total || s.net_pay" :currency="s.currency" />
						</div>
						<p v-if="s.total_deduction" class="mt-1 text-[13px] text-ink-500"><span class="text-danger">-</span> {{ formatMoney(s.total_deduction, s.currency) }}</p>
					</RouterLink>
					<div v-if="!data.recent_slips.length" class="card"><EmptyState spot="salary" description="Slips appear here once HR submits payroll." /></div>
				</div>
			</section>

			<!-- attendance -->
			<section class="mt-6">
				<div class="mb-3 flex items-baseline justify-between">
					<h2 class="section-title">Attendance</h2>
					<RouterLink to="/attendance" class="text-[13px] text-ink-500 hover:text-brand-500">Show More</RouterLink>
				</div>
				<AttendanceCalendar v-model:month="month" v-model:selected="selectedDay" :statuses="statuses" :loading="att.loading.value" legend />
				<p v-if="selectedDay" class="mt-2 text-center text-[13px] text-ink-500">{{ formatDate(selectedDay, { weekday: true }) }}: {{ statuses[selectedDay] || "Nothing recorded" }}</p>
			</section>
		</template>
	</div>
</template>
