<script setup lang="ts">
import { CalendarClock, CheckSquare, Layers, Pencil, Plus, Search, Square, UserX, Users, X } from "lucide-vue-next"
import { useMediaQuery } from "@vueuse/core"
import { computed, ref } from "vue"

import { call } from "@/api/client"
import type { PlannerEmployee, PlannerShift, PlannerShiftType, ShiftPlanner } from "@/api/types"
import AllocateSheet from "@/components/shifts/AllocateSheet.vue"
import DayTimeline from "@/components/shifts/DayTimeline.vue"
import EditShiftSheet from "@/components/shifts/EditShiftSheet.vue"
import ShiftChip from "@/components/shifts/ShiftChip.vue"
import ShiftTypeSheet from "@/components/shifts/ShiftTypeSheet.vue"
import AppBar from "@/components/ui/AppBar.vue"
import AppButton from "@/components/ui/AppButton.vue"
import Avatar from "@/components/ui/Avatar.vue"
import EmptyState from "@/components/ui/EmptyState.vue"
import ErrorState from "@/components/ui/ErrorState.vue"
import Skeleton from "@/components/ui/Skeleton.vue"
import StatTile from "@/components/ui/StatTile.vue"
import { useResource } from "@/composables/useResource"
import { formatDate, titleCase } from "@/lib/format"
import { duration, PERIODS, periodOf } from "@/lib/shifts"

const { data, error, loading, reload } = useResource((signal) => call<ShiftPlanner>("shifts.get_planner", {}, { signal }))

const isDesktop = useMediaQuery("(min-width: 1024px)")
const tab = ref<"employees" | "timings">("employees")
const search = ref("")
const department = ref("")
const shiftFilter = ref("") // "" all, "__none" without shift, else a shift type name
const quick = ref<"" | "with" | "none" | "multi">("")
const selected = ref<Set<string>>(new Set())

const employees = computed(() => data.value?.employees ?? [])
const stats = computed(() => ({
	with: employees.value.filter((e) => e.shifts.length).length,
	none: employees.value.filter((e) => !e.shifts.length).length,
	multi: employees.value.filter((e) => new Set(e.shifts.map((s) => s.shift_type)).size > 1).length,
}))

const visible = computed(() => {
	const q = search.value.trim().toLowerCase()
	return employees.value.filter((e) => {
		if (q && !`${e.employee_name} ${e.name} ${e.designation ?? ""}`.toLowerCase().includes(q)) return false
		if (department.value && e.department !== department.value) return false
		if (shiftFilter.value === "__none" && e.shifts.length) return false
		if (shiftFilter.value && shiftFilter.value !== "__none" && !e.shifts.some((s) => s.shift_type === shiftFilter.value)) return false
		if (quick.value === "with" && !e.shifts.length) return false
		if (quick.value === "none" && e.shifts.length) return false
		if (quick.value === "multi" && new Set(e.shifts.map((s) => s.shift_type)).size < 2) return false
		return true
	})
})
const filtersOn = computed(() => !!(search.value || department.value || shiftFilter.value || quick.value))
function clearFilters() {
	search.value = ""
	department.value = ""
	shiftFilter.value = ""
	quick.value = ""
}

// ---- selection
const allVisibleSelected = computed(() => visible.value.length > 0 && visible.value.every((e) => selected.value.has(e.name)))
function toggle(name: string) {
	const next = new Set(selected.value)
	if (next.has(name)) next.delete(name)
	else next.add(name)
	selected.value = next
}
function toggleAll() {
	const next = new Set(selected.value)
	if (allVisibleSelected.value) visible.value.forEach((e) => next.delete(e.name))
	else visible.value.forEach((e) => next.add(e.name))
	selected.value = next
}
function deselect(names: string[]) {
	const next = new Set(selected.value)
	names.forEach((n) => next.delete(n))
	selected.value = next
	allocTargets.value = allocTargets.value.filter((e) => !names.includes(e.name))
}

// ---- sheets
const allocOpen = ref(false)
const allocTargets = ref<PlannerEmployee[]>([])
const presetType = ref<string | null>(null)
function openAllocate(only?: PlannerEmployee) {
	allocTargets.value = only ? [only] : employees.value.filter((e) => selected.value.has(e.name))
	presetType.value = null
	allocOpen.value = true
}
function afterAllocate() {
	if (allocTargets.value.length > 1) selected.value = new Set()
	reload()
}

const editOpen = ref(false)
const editEmployee = ref<PlannerEmployee | null>(null)
const editShift = ref<PlannerShift | null>(null)
function openEdit(e: PlannerEmployee, s: PlannerShift) {
	editEmployee.value = e
	editShift.value = s
	editOpen.value = true
}

const typeOpen = ref(false)
const editType = ref<PlannerShiftType | null>(null)
function openType(t: PlannerShiftType | null) {
	editType.value = t
	typeOpen.value = true
}
function showPeopleOn(t: PlannerShiftType) {
	clearFilters()
	shiftFilter.value = t.name
	tab.value = "employees"
}

function chipSub(s: PlannerShift, today: string) {
	if (s.from_date > today) return `from ${formatDate(s.from_date, { year: false })}`
	if (s.to_date) return `till ${formatDate(s.to_date, { year: false })}`
	return s.shift_type
}

const groupedTypes = computed(() =>
	PERIODS.map((p) => ({ period: p, types: (data.value?.shift_types ?? []).filter((t) => periodOf(t.start).key === p.key) })).filter((g) => g.types.length),
)
const byName = computed(() => new Map(employees.value.map((e) => [e.name, e])))
</script>

<template>
	<div :class="selected.size && tab === 'employees' ? 'pb-20' : ''">
		<AppBar title="Shift planner" :subtitle="data ? `${employees.length} employees · ${data.shift_types.length} shift timings` : undefined">
			<template #extension>
				<nav class="flex gap-6 px-4" aria-label="Shift planner sections">
					<button
						v-for="t in [{ v: 'employees', l: 'Employees' }, { v: 'timings', l: 'Shift timings' }] as const"
						:key="t.v"
						type="button"
						class="relative flex h-11 items-center text-[16px]"
						:class="tab === t.v ? 'font-medium text-white' : 'text-white/80 hover:text-white'"
						:aria-current="tab === t.v ? 'page' : undefined"
						@click="tab = t.v"
					>
						{{ t.l }}
						<span v-if="tab === t.v" class="absolute inset-x-0 bottom-0 h-[3px] rounded-full bg-lime" aria-hidden="true" />
					</button>
				</nav>
			</template>
		</AppBar>

		<ErrorState v-if="error" :error="error" :retrying="loading" @retry="reload" />
		<template v-else-if="!data">
			<div class="mb-3 grid grid-cols-3 gap-2"><Skeleton v-for="i in 3" :key="i" card :lines="2" /></div>
			<Skeleton card :lines="10" />
		</template>

		<!-- ============================== EMPLOYEES -->
		<div v-else-if="tab === 'employees'" class="space-y-3">
			<div class="space-y-3 lg:flex lg:items-end lg:justify-between lg:gap-6 lg:space-y-0">
			<div class="grid grid-cols-3 gap-2 lg:w-[480px] lg:shrink-0">
				<StatTile label="Have shift" :value="stats.with" :icon="CalendarClock" tone="success" clickable :active="quick === 'with'" @click="quick = quick === 'with' ? '' : 'with'" />
				<StatTile label="No shift" :value="stats.none" :icon="UserX" tone="danger" clickable :active="quick === 'none'" @click="quick = quick === 'none' ? '' : 'none'" />
				<StatTile label="2+ shifts" :value="stats.multi" :icon="Layers" tone="info" clickable :active="quick === 'multi'" @click="quick = quick === 'multi' ? '' : 'multi'" />
			</div>

			<div class="flex flex-wrap gap-1.5 lg:justify-end" aria-label="Colour legend">
				<span v-for="p in PERIODS" :key="p.key" class="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium lg:px-2.5 lg:py-1 lg:text-[12px]" :class="p.chip">
					<component :is="p.icon" class="h-3 w-3" /> {{ p.label }}
				</span>
			</div>
			</div>

			<div class="grid grid-cols-2 gap-2 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)]">
			<label class="relative col-span-2 block lg:col-span-1"><span class="sr-only">Search employees</span>
				<Search class="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-400" />
				<input v-model="search" type="search" class="field h-11 rounded-full pl-11" placeholder="Search name, ID or designation" />
			</label>
				<label class="block"><span class="sr-only">Department</span>
					<select v-model="department" class="field h-11 text-sm">
						<option value="">All departments</option>
						<option v-for="d in data.departments" :key="d" :value="d">{{ d.replace(/ - BBA$/, "") }}</option>
					</select>
				</label>
				<label class="block"><span class="sr-only">Shift</span>
					<select v-model="shiftFilter" class="field h-11 text-sm">
						<option value="">All shifts</option>
						<option value="__none">Without a shift</option>
						<option v-for="t in data.shift_types" :key="t.name" :value="t.name">{{ t.name }}</option>
					</select>
				</label>
			</div>

			<div class="flex items-center justify-between rounded-xl bg-ink-50 px-2 py-1.5">
				<button type="button" class="flex items-center gap-2 rounded-lg px-1.5 py-1 text-sm font-medium text-ink-700 hover:bg-white" :disabled="!visible.length" @click="toggleAll">
					<component :is="allVisibleSelected ? CheckSquare : Square" class="h-5 w-5" :class="allVisibleSelected ? 'text-brand-500' : 'text-ink-400'" />
					{{ allVisibleSelected ? "Unselect" : "Select" }} all {{ visible.length }}
				</button>
				<button v-if="filtersOn" type="button" class="flex items-center gap-1 rounded-lg px-2 py-1 text-[13px] text-brand-600 hover:bg-white" @click="clearFilters"><X class="h-3.5 w-3.5" /> Clear filters</button>
			</div>

			<div v-if="visible.length" class="sticky top-[100px] z-10 hidden gap-x-4 border-b border-ink-200 bg-white px-3 pb-2 pt-1 text-[12px] font-medium uppercase tracking-wide text-ink-500 lg:grid lg:grid-cols-[minmax(230px,1.1fr)_minmax(0,1.15fr)_minmax(0,1.7fr)_44px]" aria-hidden="true">
				<span>Employee</span><span>Shifts</span><DayTimeline :items="[]" scale-only class="self-end normal-case tracking-normal" /><span />
			</div>
			<ul class="space-y-2.5 lg:space-y-1.5" :class="loading ? 'opacity-60' : ''">
				<li
					v-for="e in visible"
					:key="e.name"
					class="grid grid-cols-[minmax(0,1fr)_auto] rounded-2xl border bg-white p-3 shadow-card transition lg:items-center lg:gap-x-4 lg:rounded-xl lg:py-2.5 lg:shadow-none lg:hover:bg-ink-50 lg:grid-cols-[minmax(230px,1.1fr)_minmax(0,1.15fr)_minmax(0,1.7fr)_44px]"
					:class="selected.has(e.name) ? 'border-brand-500 bg-brand-50/50 ring-1 ring-brand-500 lg:hover:bg-brand-50' : 'border-ink-200'"
				>
						<button type="button" class="col-start-1 row-start-1 flex min-w-0 items-center gap-3 text-left" :aria-pressed="selected.has(e.name)" :aria-label="`Select ${e.employee_name}`" @click="toggle(e.name)">
							<span class="relative shrink-0">
								<Avatar :name="e.employee_name" :image="e.image" size="lg" />
								<span class="absolute -bottom-0.5 -right-0.5 grid h-5 w-5 place-items-center rounded-md border-2 border-white" :class="selected.has(e.name) ? 'bg-brand-500 text-white' : 'bg-ink-200'">
									<svg v-if="selected.has(e.name)" viewBox="0 0 16 16" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M3 8.5l3 3 7-7" /></svg>
								</span>
							</span>
							<span class="min-w-0">
								<span class="block truncate font-semibold">{{ titleCase(e.employee_name) }}</span>
								<span class="block truncate text-[13px] text-ink-500">{{ titleCase(e.designation) || "—" }}<template v-if="e.department"> · {{ e.department.replace(/ - BBA$/, "") }}</template></span>
							</span>
						</button>
						<button type="button" class="col-start-2 row-start-1 grid h-10 w-10 shrink-0 place-items-center self-center rounded-full bg-brand-50 text-brand-600 hover:bg-brand-100 lg:col-start-4" :aria-label="`Add a shift for ${e.employee_name}`" title="Add a shift" @click="openAllocate(e)">
							<Plus class="h-5 w-5" />
						</button>

					<div class="col-span-2 row-start-2 mt-2.5 pl-[68px] lg:col-span-1 lg:col-start-2 lg:row-start-1 lg:mt-0 lg:pl-0">
						<div v-if="e.shifts.length" class="flex flex-wrap gap-1.5">
							<ShiftChip v-for="s in e.shifts" :key="s.assignment" :start="s.start" :end="s.end" :sub="chipSub(s, data.today)" clickable :title="`Edit ${s.shift_type}`" @click="openEdit(e, s)" />
						</div>
						<button v-else type="button" class="inline-flex items-center gap-1.5 rounded-xl border border-dashed border-danger/40 bg-danger-soft/50 px-2.5 py-1.5 text-[13px] font-medium text-danger-dark hover:bg-danger-soft" @click="openAllocate(e)">
							<UserX class="h-4 w-4" /> No shift yet — add one
						</button>
					</div>
					<DayTimeline v-if="e.shifts.length" :items="e.shifts.filter((s) => s.from_date <= data!.today)" :height="isDesktop ? 'md' : 'sm'" class="col-span-2 row-start-3 mt-2 pl-[68px] lg:col-span-1 lg:col-start-3 lg:row-start-1 lg:mt-0 lg:pl-0" />
				</li>
			</ul>
			<div v-if="!visible.length" class="card">
				<EmptyState spot="team" :title="filtersOn ? 'Nobody matches' : 'No active employees'" :description="filtersOn ? 'Try another name, department or shift.' : undefined">
					<AppButton v-if="filtersOn" variant="secondary" size="sm" @click="clearFilters">Clear filters</AppButton>
				</EmptyState>
			</div>

			<!-- bulk action bar -->
			<Transition name="fade">
				<div v-if="selected.size" class="fixed inset-x-0 bottom-[84px] z-30 mx-auto max-w-app px-3 lg:bottom-6 lg:left-64 lg:max-w-xl">
					<div class="flex items-center gap-2 rounded-2xl bg-ink-900 p-2 pl-4 text-white shadow-lift">
						<Users class="h-5 w-5 shrink-0 text-lime" />
						<span class="flex-1 text-sm font-medium">{{ selected.size }} selected</span>
						<button type="button" class="rounded-lg px-2.5 py-2 text-sm text-white/80 hover:bg-white/10" @click="selected = new Set()">Clear</button>
						<button type="button" class="inline-flex items-center gap-1.5 rounded-xl bg-brand-500 px-3.5 py-2.5 text-sm font-semibold hover:bg-brand-600" @click="openAllocate()">
							<CalendarClock class="h-4 w-4" /> Allocate shift
						</button>
					</div>
				</div>
			</Transition>
		</div>

		<!-- ============================== SHIFT TIMINGS -->
		<div v-else class="space-y-5">
			<div class="lg:flex lg:items-center lg:justify-between">
				<p class="hidden text-sm text-ink-500 lg:block">Change a timing here to change it for everyone on that shift.</p>
				<AppButton block variant="secondary" class="lg:w-auto" @click="openType(null)"><Plus class="h-5 w-5" /> New shift timing</AppButton>
			</div>
			<EmptyState v-if="!data.shift_types.length" spot="attendance" title="No shift timings yet" description="Create one, then allocate it from the Employees tab." />
			<section v-for="g in groupedTypes" :key="g.period.key">
				<h2 class="mb-2 flex items-center gap-2 text-[15px] font-semibold">
					<span class="grid h-7 w-7 place-items-center rounded-lg" :class="g.period.soft"><component :is="g.period.icon" class="h-4 w-4" /></span>
					{{ g.period.label }} <span class="text-[13px] font-normal text-ink-500">{{ g.types.length }}</span>
				</h2>
				<ul class="grid gap-2.5 sm:grid-cols-2 xl:grid-cols-3">
					<li v-for="t in g.types" :key="t.name" class="card flex flex-col p-3">
						<div class="flex items-start gap-3">
							<div class="min-w-0 flex-1">
								<ShiftChip :start="t.start" :end="t.end" />
								<p class="mt-1.5 truncate text-[13px] font-medium text-ink-800">{{ t.name }}</p>
								<p class="text-[12px] text-ink-500">{{ duration(t.start, t.end) }}</p>
							</div>
							<button type="button" class="inline-flex shrink-0 items-center gap-1 rounded-xl border border-ink-200 px-2.5 py-1.5 text-[13px] font-medium text-brand-600 hover:bg-brand-50" @click="openType(t)">
								<Pencil class="h-3.5 w-3.5" /> Timing
							</button>
						</div>
						<DayTimeline :items="[{ start: t.start, end: t.end }]" scale class="mt-2.5" />
						<button v-if="t.employees.length" type="button" class="mt-2.5 flex w-full items-center gap-2 rounded-xl bg-ink-50 px-2 py-1.5 text-left hover:bg-ink-100" @click="showPeopleOn(t)">
							<span class="flex -space-x-2">
								<Avatar v-for="n in t.employees.slice(0, 5)" :key="n" :name="byName.get(n)?.employee_name" :image="byName.get(n)?.image" size="sm" class="ring-2 ring-white" />
							</span>
							<span class="flex-1 text-[13px] text-ink-700">{{ t.employees.length }} {{ t.employees.length === 1 ? "person" : "people" }}</span>
							<span class="text-[12px] font-medium text-brand-600">View</span>
						</button>
						<p v-else class="mt-auto pt-2.5 text-[12px] text-ink-400">Nobody on this shift right now</p>
					</li>
				</ul>
			</section>
		</div>

		<AllocateSheet v-if="data" v-model="allocOpen" :employees="allocTargets" :shift-types="data.shift_types" :today="data.today" :preset-type="presetType" @saved="afterAllocate" @deselect="deselect" />
		<EditShiftSheet v-if="data" v-model="editOpen" :employee="editEmployee" :shift="editShift" :today="data.today" @saved="reload" />
		<ShiftTypeSheet v-if="data" v-model="typeOpen" :type="editType" :employees="employees" :existing-names="data.shift_types.map((t) => t.name)" @saved="reload" />
	</div>
</template>
