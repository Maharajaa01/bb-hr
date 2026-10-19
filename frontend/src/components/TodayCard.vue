<script setup lang="ts">
import { Clock, Fingerprint, LogIn, LogOut, PartyPopper, Timer } from "lucide-vue-next"
import { computed } from "vue"

import type { AttendanceStatus } from "@/api/types"
import AppButton from "@/components/ui/AppButton.vue"
import StatusBadge from "@/components/ui/StatusBadge.vue"
import { formatDate, formatHours, formatTime } from "@/lib/format"

const props = defineProps<{ status: AttendanceStatus; showAction?: boolean }>()

const label = computed(() => {
	const s = props.status
	if (s.attendance) return s.attendance.status
	if (s.checked_in) return "In Now"
	if (s.logs.length) return "Present"
	if (s.holiday) return "Holiday"
	return "Not Marked"
})
</script>

<template>
	<section class="card overflow-hidden">
		<div class="bg-gradient-to-br from-brand-500 to-brand-700 px-5 pb-5 pt-4 text-white">
			<div class="flex items-center justify-between">
				<p class="text-sm text-brand-50">{{ formatDate(status.date, { weekday: true }) }}</p>
				<StatusBadge :status="label" />
			</div>
			<div v-if="status.holiday" class="mt-3 flex items-center gap-2 rounded-xl bg-white/15 px-3 py-2 text-sm text-white">
				<PartyPopper class="h-4 w-4" /> {{ status.holiday.weekly_off ? "Weekly off" : status.holiday.description }}
			</div>
			<div class="mt-4 grid grid-cols-3 gap-3">
				<div>
					<p class="flex items-center gap-1 text-xs text-brand-100"><LogIn class="h-3.5 w-3.5" /> First in</p>
					<p class="tabular mt-1 text-lg font-bold">{{ formatTime(status.first_in) }}</p>
				</div>
				<div>
					<p class="flex items-center gap-1 text-xs text-brand-100"><LogOut class="h-3.5 w-3.5" /> Last out</p>
					<p class="tabular mt-1 text-lg font-bold">{{ formatTime(status.last_out) }}</p>
				</div>
				<div>
					<p class="flex items-center gap-1 text-xs text-brand-100"><Timer class="h-3.5 w-3.5" /> Worked</p>
					<p class="tabular mt-1 text-lg font-bold">{{ formatHours(status.worked_hours) }}</p>
				</div>
			</div>
		</div>
		<div class="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
			<div class="min-w-0 text-sm text-ink-600">
				<p v-if="status.shift?.name" class="flex items-center gap-1.5"><Clock class="h-4 w-4 text-brand-500" /> Shift {{ formatTime(status.shift.start) }} – {{ formatTime(status.shift.end) }}</p>
				<p v-else class="flex items-center gap-1.5"><Clock class="h-4 w-4 text-brand-500" /> No shift assigned</p>
				<p v-if="status.late_minutes > 0" class="mt-0.5 text-amber-700">Arrived {{ status.late_minutes }} min late</p>
				<p v-if="status.logs.length" class="mt-0.5 text-ink-500">{{ status.logs.length }} punch{{ status.logs.length === 1 ? "" : "es" }} today</p>
			</div>
			<AppButton v-if="showAction" to="/check-in" :variant="status.checked_in ? 'primary' : 'accent'">
				<Fingerprint class="h-5 w-5" /> {{ status.checked_in ? "Check out" : "Check in" }}
			</AppButton>
		</div>
	</section>
</template>
