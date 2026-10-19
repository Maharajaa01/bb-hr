<script setup lang="ts">
import { Clock, RefreshCw } from "lucide-vue-next"

/** Check In · Check Out · Duration, one row per punch pair. */
defineProps<{ rows: { key: string; in: string; out: string; duration: string }[]; empty?: string }>()
</script>

<template>
	<table class="w-full text-[14px]">
		<thead>
			<tr class="bg-ink-100 text-left text-ink-700">
				<th class="px-3 py-2.5 font-medium">Check In</th>
				<th class="px-3 py-2.5 font-medium">Check Out</th>
				<th class="px-3 py-2.5 font-medium">Duration</th>
			</tr>
		</thead>
		<tbody class="tabular">
			<tr v-for="r in rows" :key="r.key" class="border-b border-ink-200">
				<td class="px-3 py-2.5"><span class="inline-flex items-center gap-1.5"><Clock class="h-4 w-4 text-brand-500" />{{ r.in }}</span></td>
				<td class="px-3 py-2.5"><span class="inline-flex items-center gap-1.5"><Clock class="h-4 w-4 text-danger" />{{ r.out }}</span></td>
				<td class="px-3 py-2.5"><span class="inline-flex items-center gap-1.5"><RefreshCw class="h-4 w-4 text-success" />{{ r.duration }}</span></td>
			</tr>
			<tr v-if="!rows.length"><td colspan="3" class="px-3 py-4 text-center text-[13px] text-ink-500">{{ empty ?? "No punches yet" }}</td></tr>
		</tbody>
	</table>
</template>
