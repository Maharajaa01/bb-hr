<script setup lang="ts">
import { CalendarDays, Info, Save, Trash2 } from "lucide-vue-next"
import { computed, ref, watch } from "vue"

import { ApiError, call } from "@/api/client"
import type { PlannerEmployee, PlannerShift, ShiftConflict, ShiftSaveResult } from "@/api/types"
import AppButton from "@/components/ui/AppButton.vue"
import Avatar from "@/components/ui/Avatar.vue"
import Sheet from "@/components/ui/Sheet.vue"
import { formatDate, titleCase } from "@/lib/format"
import { datesOverlap, timeRange, timesOverlap } from "@/lib/shifts"
import { useToasts } from "@/stores/toast"

import ConflictList from "./ConflictList.vue"
import DayTimeline, { type TimelineItem } from "./DayTimeline.vue"
import TimeRangeInput from "./TimeRangeInput.vue"

const props = defineProps<{ employee: PlannerEmployee | null; shift: PlannerShift | null; today: string }>()
const emit = defineEmits<{ saved: [] }>()
const open = defineModel<boolean>({ required: true })
const toasts = useToasts()

const start = ref("")
const end = ref("")
const fromDate = ref("")
const toDate = ref("")
const saving = ref(false)
const removing = ref(false)
const confirmRemove = ref(false)
const serverConflicts = ref<ShiftConflict[]>([])
const serverError = ref("")

watch(open, (v) => {
	if (!v || !props.shift) return
	start.value = props.shift.start
	end.value = props.shift.end
	fromDate.value = props.shift.from_date
	toDate.value = props.shift.to_date ?? ""
	confirmRemove.value = false
	serverConflicts.value = []
	serverError.value = ""
})
watch([start, end, fromDate, toDate], () => {
	serverConflicts.value = []
	serverError.value = ""
})

const started = computed(() => !!props.shift && props.shift.from_date <= props.today)
const timingChanged = computed(() => !!props.shift && (start.value !== props.shift.start || end.value !== props.shift.end))
const effectiveFrom = computed(() => (started.value && timingChanged.value ? props.today : fromDate.value))
const changed = computed(() => !!props.shift && (timingChanged.value || fromDate.value !== props.shift.from_date || (toDate.value || null) !== props.shift.to_date))
const valid = computed(() => !!start.value && !!end.value && start.value !== end.value && !!fromDate.value && (!toDate.value || toDate.value >= effectiveFrom.value))

const others = computed(() => (props.employee?.shifts ?? []).filter((s) => s.assignment !== props.shift?.assignment))
const localConflicts = computed<ShiftConflict[]>(() => {
	if (!props.employee || !valid.value) return []
	const clash = others.value.filter((s) => datesOverlap(effectiveFrom.value, toDate.value || null, s.from_date, s.to_date) && timesOverlap({ start: start.value, end: end.value }, s))
	return clash.length ? [{ employee: props.employee.name, employee_name: props.employee.employee_name, conflicts: clash }] : []
})
const conflicts = computed(() => (serverConflicts.value.length ? serverConflicts.value : localConflicts.value))

const timeline = computed<TimelineItem[]>(() => {
	const items: TimelineItem[] = others.value.map((s) => ({ start: s.start, end: s.end, label: s.shift_type }))
	if (start.value && end.value && start.value !== end.value) items.push({ start: start.value, end: end.value, tone: conflicts.value.length ? "conflict" : "new", label: "This shift" })
	return items
})

async function save() {
	if (!props.shift || !valid.value || conflicts.value.length) return
	saving.value = true
	try {
		const res = await call<ShiftSaveResult>(
			"shifts.update_assignment",
			{ assignment: props.shift.assignment, start_time: start.value, end_time: end.value, from_date: fromDate.value, to_date: toDate.value || null },
			{ method: "POST" },
		)
		if (!res.ok) {
			serverConflicts.value = res.conflicts ?? []
			return
		}
		toasts.success("Shift updated", res.message)
		open.value = false
		emit("saved")
	} catch (e) {
		serverError.value = e instanceof ApiError ? e.message : String(e)
	} finally {
		saving.value = false
	}
}

async function remove() {
	if (!props.shift) return
	if (!confirmRemove.value) {
		confirmRemove.value = true
		return
	}
	removing.value = true
	try {
		await call("shifts.end_assignment", { assignment: props.shift.assignment }, { method: "POST" })
		toasts.success("Shift removed", started.value ? "Earlier days keep this shift." : undefined)
		open.value = false
		emit("saved")
	} catch (e) {
		serverError.value = e instanceof ApiError ? e.message : String(e)
	} finally {
		removing.value = false
	}
}
</script>

<template>
	<Sheet v-model="open" title="Edit shift">
		<div v-if="employee && shift" class="space-y-5">
			<div class="flex items-center gap-3 rounded-2xl bg-brand-50 p-3">
				<Avatar :name="employee.employee_name" :image="employee.image" size="lg" />
				<div class="min-w-0">
					<p class="truncate font-semibold">{{ titleCase(employee.employee_name) }}</p>
					<p class="truncate text-[13px] text-ink-600">{{ titleCase(employee.designation) || employee.name }}</p>
					<p class="truncate text-[12px] text-ink-500">Now: {{ timeRange(shift.start, shift.end) }} · {{ shift.shift_type }}</p>
				</div>
			</div>

			<TimeRangeInput v-model:start="start" v-model:end="end" />

			<section class="grid grid-cols-2 gap-3">
				<label class="block">
					<span class="label flex items-center gap-1"><CalendarDays class="h-3.5 w-3.5" /> From</span>
					<input v-model="fromDate" type="date" class="field" :disabled="started" />
				</label>
				<label class="block">
					<span class="label">Until <span class="text-ink-400">(optional)</span></span>
					<input v-model="toDate" type="date" :min="effectiveFrom" class="field" />
				</label>
			</section>

			<p v-if="started && timingChanged" class="flex gap-2 rounded-xl bg-sky-50 p-3 text-[13px] text-sky-900">
				<Info class="mt-0.5 h-4 w-4 shrink-0" />
				<span>The new timing applies from <b>today</b>. Days before today stay on {{ timeRange(shift.start, shift.end) }}, so past attendance is not changed.</span>
			</p>
			<p v-else-if="started" class="text-[12px] text-ink-500">Running since {{ formatDate(shift.from_date) }}, so the start date is fixed.</p>

			<section>
				<p class="label">{{ titleCase(employee.employee_name).split(" ")[0] }}'s day</p>
				<div class="rounded-2xl bg-ink-50 p-3"><DayTimeline :items="timeline" scale height="md" /></div>
			</section>

			<ConflictList v-if="conflicts.length" :conflicts="conflicts" />
			<p v-if="serverError" class="rounded-xl bg-danger-soft p-3 text-sm text-danger-dark" role="alert">{{ serverError }}</p>
			<p class="text-[12px] text-ink-500">This changes only {{ titleCase(employee.employee_name).split(" ")[0] }}'s shift. To change “{{ shift.shift_type }}” for everyone on it, use the Shift timings tab.</p>

			<div class="flex flex-col gap-2">
				<AppButton block :loading="saving" :disabled="!changed || !valid || !!conflicts.length" @click="save"><Save class="h-5 w-5" /> Save changes</AppButton>
				<AppButton block :variant="confirmRemove ? 'danger' : 'secondary'" :loading="removing" @click="remove">
					<Trash2 class="h-4 w-4" /> {{ confirmRemove ? "Tap again to remove this shift" : "Remove shift" }}
				</AppButton>
			</div>
		</div>
	</Sheet>
</template>
