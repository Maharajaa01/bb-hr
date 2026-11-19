<script setup lang="ts">
import { AlertOctagon } from "lucide-vue-next"

import type { ShiftConflict } from "@/api/types"
import { formatDate, titleCase } from "@/lib/format"
import { timeRange } from "@/lib/shifts"

/** Who clashes with what, as returned by api/shifts.py (or worked out in the browser). */
defineProps<{ conflicts: ShiftConflict[]; title?: string }>()
</script>

<template>
	<div class="rounded-2xl border border-danger/30 bg-danger-soft p-3.5" role="alert">
		<p class="mb-2 flex items-center gap-2 text-sm font-semibold text-danger-dark">
			<AlertOctagon class="h-4 w-4 shrink-0" /> {{ title ?? "Timings overlap" }}
		</p>
		<ul class="space-y-1.5 text-[13px] text-ink-800">
			<li v-for="c in conflicts" :key="c.employee">
				<span class="font-medium">{{ titleCase(c.employee_name) }}</span>
				<span class="text-ink-600"> already works </span>
				<span v-for="(x, i) in c.conflicts" :key="x.assignment">
					<span v-if="i" class="text-ink-600">, </span>
					<span class="tabular font-medium">{{ timeRange(x.start, x.end) }}</span>
					<span class="text-ink-500"> ({{ x.to_date ? `till ${formatDate(x.to_date, { year: false })}` : `from ${formatDate(x.from_date, { year: false })}` }})</span>
				</span>
			</li>
		</ul>
	</div>
</template>
