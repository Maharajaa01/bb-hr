<script setup lang="ts">
import { periodOf, segments, timeRange } from "@/lib/shifts"

export interface TimelineItem {
	start: string
	end: string
	/** new = the shift being added (striped), conflict = clashes (red) */
	tone?: "normal" | "new" | "conflict" | "muted"
	label?: string
}

/** A 24-hour bar with each shift drawn where it falls in the day. */
withDefaults(defineProps<{ items: TimelineItem[]; scale?: boolean; scaleOnly?: boolean; height?: "sm" | "md" }>(), { height: "sm" })

const TICKS = [0, 6, 12, 18, 24]
function tickLabel(h: number) {
	return h === 0 || h === 24 ? "12a" : h === 12 ? "12p" : h < 12 ? `${h}a` : `${h - 12}p`
}
function color(item: TimelineItem) {
	if (item.tone === "conflict") return "bg-danger"
	if (item.tone === "muted") return "bg-ink-300"
	return periodOf(item.start).bar
}
</script>

<template>
	<div>
		<div
			v-if="!scaleOnly"
			class="relative overflow-hidden rounded-full bg-ink-100"
			:class="height === 'md' ? 'h-4' : 'h-2'"
			role="img"
			:aria-label="items.length ? items.map((i) => (i.label ? `${i.label} ` : '') + timeRange(i.start, i.end)).join(', ') : 'No shifts'"
		>
			<span v-for="h in [6, 12, 18]" :key="h" class="absolute inset-y-0 w-px bg-white" :style="{ left: `${(h / 24) * 100}%` }" />
			<template v-for="(item, i) in items" :key="i">
				<span
					v-for="(seg, j) in segments(item.start, item.end)"
					:key="j"
					class="absolute inset-y-0 rounded-full"
					:class="[color(item), item.tone === 'new' ? 'stripes ring-2 ring-inset ring-white/60' : '']"
					:style="{ left: `${seg.left}%`, width: `${Math.max(seg.width, 0.8)}%` }"
					:title="(item.label ? `${item.label}: ` : '') + timeRange(item.start, item.end)"
				/>
			</template>
		</div>
		<div v-if="scale || scaleOnly" class="relative h-3 text-[10px] text-ink-400" :class="scaleOnly ? '' : 'mt-1'" aria-hidden="true">
			<span v-for="h in TICKS" :key="h" class="absolute -translate-x-1/2" :class="h === 0 ? 'translate-x-0' : h === 24 ? '-translate-x-full' : ''" :style="{ left: `${(h / 24) * 100}%` }">{{ tickLabel(h) }}</span>
		</div>
	</div>
</template>

<style scoped>
.stripes {
	background-image: repeating-linear-gradient(135deg, rgba(255, 255, 255, 0.45) 0 4px, transparent 4px 8px);
}
</style>
