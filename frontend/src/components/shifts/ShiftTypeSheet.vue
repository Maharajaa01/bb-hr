<script setup lang="ts">
import { AlertTriangle, Save } from "lucide-vue-next"
import { computed, ref, watch } from "vue"

import { ApiError, call } from "@/api/client"
import type { PlannerEmployee, PlannerShiftType, ShiftConflict, ShiftSaveResult } from "@/api/types"
import AppButton from "@/components/ui/AppButton.vue"
import Avatar from "@/components/ui/Avatar.vue"
import Sheet from "@/components/ui/Sheet.vue"
import { titleCase } from "@/lib/format"
import { datesOverlap, timeRange, timesOverlap } from "@/lib/shifts"
import { useToasts } from "@/stores/toast"

import ConflictList from "./ConflictList.vue"
import DayTimeline from "./DayTimeline.vue"
import TimeRangeInput from "./TimeRangeInput.vue"

/** Create a shift timing, or change the timing of one for everybody on it. */
const props = defineProps<{ type: PlannerShiftType | null; employees: PlannerEmployee[]; existingNames: string[] }>()
const emit = defineEmits<{ saved: [] }>()
const open = defineModel<boolean>({ required: true })
const toasts = useToasts()

const start = ref("09:00")
const end = ref("13:00")
const name = ref("")
const saving = ref(false)
const serverConflicts = ref<ShiftConflict[]>([])
const serverError = ref("")

watch(open, (v) => {
	if (!v) return
	start.value = props.type?.start ?? "09:00"
	end.value = props.type?.end ?? "13:00"
	name.value = ""
	serverConflicts.value = []
	serverError.value = ""
})
watch([start, end, name], () => {
	serverConflicts.value = []
	serverError.value = ""
})

const people = computed(() => (props.type ? props.employees.filter((e) => props.type!.employees.includes(e.name)) : []))
const nameTaken = computed(() => !props.type && !!name.value.trim() && props.existingNames.includes(name.value.trim()))
const changed = computed(() => !props.type || start.value !== props.type.start || end.value !== props.type.end)
const valid = computed(() => !!start.value && !!end.value && start.value !== end.value && !nameTaken.value)

const localConflicts = computed<ShiftConflict[]>(() => {
	if (!props.type || !valid.value) return []
	const t = { start: start.value, end: end.value }
	return people.value
		.map((e) => {
			const mine = e.shifts.filter((s) => s.shift_type === props.type!.name)
			const clash = e.shifts.filter((s) => s.shift_type !== props.type!.name && mine.some((m) => datesOverlap(m.from_date, m.to_date, s.from_date, s.to_date)) && timesOverlap(t, s))
			return { employee: e.name, employee_name: e.employee_name, conflicts: clash }
		})
		.filter((c) => c.conflicts.length)
})
const conflicts = computed(() => (serverConflicts.value.length ? serverConflicts.value : localConflicts.value))

async function save() {
	if (!valid.value || !changed.value || conflicts.value.length) return
	saving.value = true
	try {
		const res = await call<ShiftSaveResult>(
			"shifts.save_shift_type",
			{ name: props.type?.name ?? null, start_time: start.value, end_time: end.value, shift_name: name.value.trim() || null },
			{ method: "POST" },
		)
		if (!res.ok) {
			serverConflicts.value = res.conflicts ?? []
			return
		}
		toasts.success(props.type ? "Shift timing changed" : "Shift timing saved", `${res.name} · ${timeRange(start.value, end.value)}`)
		open.value = false
		emit("saved")
	} catch (e) {
		serverError.value = e instanceof ApiError ? e.message : String(e)
	} finally {
		saving.value = false
	}
}
</script>

<template>
	<Sheet v-model="open" :title="type ? 'Change shift timing' : 'New shift timing'">
		<div class="space-y-5">
			<p v-if="type" class="font-semibold">{{ type.name }}</p>
			<label v-else class="block">
				<span class="label">Name <span class="text-ink-400">(optional)</span></span>
				<input v-model="name" type="text" maxlength="120" class="field" :placeholder="`BBA ${start}-${end}`" />
				<span v-if="nameTaken" class="mt-1 block text-[13px] text-danger">That name is already used.</span>
			</label>

			<TimeRangeInput v-model:start="start" v-model:end="end" />
			<div class="rounded-2xl bg-ink-50 p-3"><DayTimeline :items="start !== end ? [{ start, end, tone: conflicts.length ? 'conflict' : 'new' }] : []" scale height="md" /></div>

			<div v-if="type && people.length && changed" class="flex gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-[13px] text-amber-900">
				<AlertTriangle class="mt-0.5 h-4 w-4 shrink-0" />
				<div>
					<p>This changes the timing for <b>all {{ people.length }}</b> {{ people.length === 1 ? "person" : "people" }} on this shift:</p>
					<div class="mt-2 flex flex-wrap gap-1">
						<span v-for="e in people.slice(0, 10)" :key="e.name" class="inline-flex items-center gap-1 rounded-full bg-white py-0.5 pl-0.5 pr-2 text-[12px]">
							<Avatar :name="e.employee_name" :image="e.image" size="sm" class="!h-5 !w-5 !text-[10px]" />{{ titleCase(e.employee_name).split(" ")[0] }}
						</span>
						<span v-if="people.length > 10" class="px-1 text-[12px]">+{{ people.length - 10 }}</span>
					</div>
					<p class="mt-2 text-[12px]">To change just one person, open their shift from the Employees tab instead.</p>
				</div>
			</div>

			<ConflictList v-if="conflicts.length" :conflicts="conflicts" title="The new timing would overlap other shifts" />
			<p v-if="serverError" class="rounded-xl bg-danger-soft p-3 text-sm text-danger-dark" role="alert">{{ serverError }}</p>

			<AppButton block :loading="saving" :disabled="!valid || !changed || !!conflicts.length" @click="save"><Save class="h-5 w-5" /> {{ type ? "Change timing" : "Save shift timing" }}</AppButton>
		</div>
	</Sheet>
</template>
