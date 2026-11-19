<script setup lang="ts">
import { CalendarDays, Check, Search, Sparkles } from "lucide-vue-next"
import { computed, ref, watch } from "vue"

import { ApiError, call } from "@/api/client"
import type { PlannerEmployee, PlannerShiftType, ShiftConflict, ShiftSaveResult } from "@/api/types"
import AppButton from "@/components/ui/AppButton.vue"
import Avatar from "@/components/ui/Avatar.vue"
import Segmented from "@/components/ui/Segmented.vue"
import Sheet from "@/components/ui/Sheet.vue"
import { titleCase } from "@/lib/format"
import { datesOverlap, duration, timeRange, timesOverlap, toMinutes } from "@/lib/shifts"
import { useToasts } from "@/stores/toast"

import ConflictList from "./ConflictList.vue"
import DayTimeline, { type TimelineItem } from "./DayTimeline.vue"
import ShiftChip from "./ShiftChip.vue"
import TimeRangeInput from "./TimeRangeInput.vue"

const props = defineProps<{ employees: PlannerEmployee[]; shiftTypes: PlannerShiftType[]; today: string; presetType?: string | null }>()
const emit = defineEmits<{ saved: []; deselect: [names: string[]] }>()
const open = defineModel<boolean>({ required: true })
const toasts = useToasts()

const mode = ref<"existing" | "new">("existing")
const typeName = ref<string | null>(null)
const start = ref("09:00")
const end = ref("13:00")
const newName = ref("")
const fromDate = ref(props.today)
const toDate = ref("")
const typeSearch = ref("")
const saving = ref(false)
const serverConflicts = ref<ShiftConflict[]>([])
const serverError = ref("")

watch(open, (v) => {
	if (!v) return
	serverConflicts.value = []
	serverError.value = ""
	fromDate.value = props.today
	toDate.value = ""
	typeName.value = props.presetType ?? null
	mode.value = props.presetType || props.shiftTypes.length ? "existing" : "new"
})

const chosenType = computed(() => props.shiftTypes.find((t) => t.name === typeName.value) ?? null)
const timing = computed(() => (mode.value === "existing" ? (chosenType.value ? { start: chosenType.value.start, end: chosenType.value.end } : null) : { start: start.value, end: end.value }))
const timingValid = computed(() => !!timing.value && !Number.isNaN(toMinutes(timing.value.start)) && !Number.isNaN(toMinutes(timing.value.end)) && timing.value.start !== timing.value.end)
const sameTimes = computed(() => (mode.value === "new" ? props.shiftTypes.find((t) => t.start === start.value && t.end === end.value) : undefined))
const datesValid = computed(() => !!fromDate.value && (!toDate.value || toDate.value >= fromDate.value))

const filteredTypes = computed(() => {
	const q = typeSearch.value.trim().toLowerCase()
	return q ? props.shiftTypes.filter((t) => t.name.toLowerCase().includes(q) || timeRange(t.start, t.end).toLowerCase().includes(q)) : props.shiftTypes
})

/** Worked out in the browser for instant feedback; the server checks again (including past allocations). */
const localConflicts = computed<ShiftConflict[]>(() => {
	if (!timingValid.value || !datesValid.value) return []
	const t = timing.value!
	const to = toDate.value || null
	return props.employees
		.map((e) => ({
			employee: e.name,
			employee_name: e.employee_name,
			conflicts: e.shifts
				.filter((s) => datesOverlap(fromDate.value, to, s.from_date, s.to_date) && timesOverlap(t, s))
				.map((s) => ({ assignment: s.assignment, shift_type: s.shift_type, start: s.start, end: s.end, from_date: s.from_date, to_date: s.to_date })),
		}))
		.filter((c) => c.conflicts.length)
})
const conflicts = computed(() => (serverConflicts.value.length ? serverConflicts.value : localConflicts.value))
const conflictNames = computed(() => new Set(conflicts.value.map((c) => c.employee)))

function timelineFor(e: PlannerEmployee): TimelineItem[] {
	const to = toDate.value || null
	const items: TimelineItem[] = e.shifts
		.filter((s) => datesOverlap(fromDate.value, to, s.from_date, s.to_date))
		.map((s) => ({ start: s.start, end: s.end, label: s.shift_type }))
	if (timingValid.value) items.push({ ...timing.value!, tone: conflictNames.value.has(e.name) ? "conflict" : "new", label: "New shift" })
	return items
}

const canSave = computed(() => timingValid.value && datesValid.value && props.employees.length > 0 && !conflicts.value.length)

watch([mode, typeName, start, end, fromDate, toDate], () => {
	serverConflicts.value = []
	serverError.value = ""
})

async function save() {
	if (!canSave.value) return
	saving.value = true
	serverError.value = ""
	try {
		const args: Record<string, unknown> = { employees: props.employees.map((e) => e.name), from_date: fromDate.value, to_date: toDate.value || null }
		if (mode.value === "existing") args.shift_type = typeName.value
		else Object.assign(args, { start_time: start.value, end_time: end.value, shift_name: newName.value.trim() || null })
		const res = await call<ShiftSaveResult>("shifts.allocate", args, { method: "POST" })
		if (!res.ok) {
			serverConflicts.value = res.conflicts ?? []
			return
		}
		toasts.success(`Shift allocated to ${res.created} ${res.created === 1 ? "employee" : "employees"}`, `${timeRange(timing.value!.start, timing.value!.end)} · ${res.shift_type}`)
		if (res.enabled_multiple) toasts.info("Multiple shifts turned on", "HR Settings now allows more than one shift per day.")
		open.value = false
		emit("saved")
	} catch (e) {
		serverError.value = e instanceof ApiError ? e.message : String(e)
	} finally {
		saving.value = false
	}
}

function skipConflicting() {
	emit("deselect", [...conflictNames.value])
	serverConflicts.value = []
}
</script>

<template>
	<Sheet v-model="open" title="Allocate shift" size="lg">
		<div class="space-y-5">
			<!-- who -->
			<section>
				<p class="label">Employees ({{ employees.length }})</p>
				<div class="flex flex-wrap gap-1.5">
					<span v-for="e in employees.slice(0, 8)" :key="e.name" class="inline-flex items-center gap-1.5 rounded-full py-0.5 pl-0.5 pr-2.5 text-[13px]" :class="conflictNames.has(e.name) ? 'bg-danger-soft text-danger-dark' : 'bg-brand-50 text-brand-800'">
						<Avatar :name="e.employee_name" :image="e.image" size="sm" class="!h-6 !w-6 !text-xs" />
						{{ titleCase(e.employee_name).split(" ")[0] }}
					</span>
					<span v-if="employees.length > 8" class="rounded-full bg-ink-100 px-2.5 py-1 text-[13px] text-ink-600">+{{ employees.length - 8 }} more</span>
				</div>
			</section>

			<!-- which timing -->
			<section>
				<div class="mb-2 flex items-center justify-between">
					<p class="label !mb-0">Shift timing</p>
					<Segmented v-model="mode" label="Shift timing source" :options="[{ value: 'existing', label: 'Saved shifts' }, { value: 'new', label: 'New timing' }]" />
				</div>
				<template v-if="mode === 'existing'">
					<label v-if="shiftTypes.length > 6" class="relative mb-2 block"><span class="sr-only">Search shifts</span>
						<Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" />
						<input v-model="typeSearch" type="search" class="field h-10 pl-9 text-sm" placeholder="Search shifts" />
					</label>
					<div class="max-h-56 space-y-1.5 overflow-y-auto pr-1" role="radiogroup" aria-label="Saved shifts">
						<button
							v-for="t in filteredTypes"
							:key="t.name"
							type="button"
							role="radio"
							:aria-checked="typeName === t.name"
							class="flex w-full items-center gap-3 rounded-xl border p-2 text-left transition"
							:class="typeName === t.name ? 'border-brand-500 bg-brand-50' : 'border-ink-200 hover:border-brand-300'"
							@click="typeName = t.name"
						>
							<ShiftChip :start="t.start" :end="t.end" />
							<span class="min-w-0 flex-1">
								<span class="block truncate text-[13px] font-medium">{{ t.name }}</span>
								<span class="block text-[12px] text-ink-500">{{ duration(t.start, t.end) }} · {{ t.employees.length }} {{ t.employees.length === 1 ? "person" : "people" }}</span>
							</span>
							<Check v-if="typeName === t.name" class="h-5 w-5 shrink-0 text-brand-500" />
						</button>
						<p v-if="!filteredTypes.length" class="py-4 text-center text-sm text-ink-500">No saved shift matches. Try "New timing".</p>
					</div>
				</template>
				<template v-else>
					<TimeRangeInput v-model:start="start" v-model:end="end" />
					<p v-if="sameTimes" class="mt-2 flex items-center gap-1.5 text-[13px] text-brand-700"><Sparkles class="h-3.5 w-3.5" /> Same as saved shift “{{ sameTimes.name }}” — it will be reused.</p>
					<label v-else class="mt-3 block">
						<span class="label">Shift name <span class="text-ink-400">(optional)</span></span>
						<input v-model="newName" type="text" maxlength="120" class="field" :placeholder="`BBA ${start}-${end}`" />
					</label>
				</template>
			</section>

			<!-- when -->
			<section class="grid grid-cols-2 gap-3">
				<label class="block">
					<span class="label flex items-center gap-1"><CalendarDays class="h-3.5 w-3.5" /> From</span>
					<input v-model="fromDate" type="date" required class="field" />
				</label>
				<label class="block">
					<span class="label">Until <span class="text-ink-400">(optional)</span></span>
					<input v-model="toDate" type="date" :min="fromDate" class="field" />
				</label>
				<p v-if="!datesValid" class="col-span-2 -mt-1 text-[13px] text-danger">“Until” must be on or after “From”.</p>
				<p v-else-if="!toDate" class="col-span-2 -mt-1 text-[12px] text-ink-500">No end date: the shift continues until you change it.</p>
			</section>

			<!-- preview -->
			<section v-if="timingValid">
				<p class="label">Day preview</p>
				<div class="space-y-2.5 rounded-2xl bg-ink-50 p-3">
					<div v-for="e in employees.slice(0, 6)" :key="e.name" class="flex items-center gap-2.5">
						<Avatar :name="e.employee_name" :image="e.image" size="sm" />
						<div class="min-w-0 flex-1">
							<p class="mb-1 truncate text-[12px] font-medium" :class="conflictNames.has(e.name) ? 'text-danger-dark' : 'text-ink-700'">{{ titleCase(e.employee_name) }}</p>
							<DayTimeline :items="timelineFor(e)" />
						</div>
					</div>
					<p v-if="employees.length > 6" class="text-center text-[12px] text-ink-500">and {{ employees.length - 6 }} more</p>
					<DayTimeline :items="[]" scale-only class="pl-[42px]" />
				</div>
			</section>

			<ConflictList v-if="conflicts.length" :conflicts="conflicts" :title="`${conflicts.length} ${conflicts.length === 1 ? 'employee clashes' : 'employees clash'} with this timing`" />
			<p v-if="serverError" class="rounded-xl bg-danger-soft p-3 text-sm text-danger-dark" role="alert">{{ serverError }}</p>

			<div class="flex flex-col gap-2">
				<AppButton block :loading="saving" :disabled="!canSave" @click="save">
					<Check class="h-5 w-5" /> Allocate to {{ employees.length }} {{ employees.length === 1 ? "employee" : "employees" }}
				</AppButton>
				<AppButton v-if="conflicts.length && conflicts.length < employees.length" block variant="secondary" @click="skipConflicting">
					Leave out the {{ conflicts.length }} with clashes
				</AppButton>
			</div>
		</div>
	</Sheet>
</template>
