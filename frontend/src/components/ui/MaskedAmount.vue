<script setup lang="ts">
import { Eye, EyeOff } from "lucide-vue-next"
import { computed, ref } from "vue"

import { formatMoney } from "@/lib/format"

/** Pay amounts are masked until tapped ("₹ ***72.**"), so a glance over the shoulder shows nothing. */
const props = defineProps<{ amount: number; currency?: string }>()
const shown = ref(false)
const masked = computed(() => {
	const full = formatMoney(props.amount, props.currency || "INR")
	const digits = Math.round(props.amount).toString()
	return `${full.replace(/[\d,.]+/, "")} ***${digits.slice(-2)}.**`
})
</script>

<template>
	<button type="button" class="tabular inline-flex items-center gap-1.5 font-semibold" :aria-label="shown ? 'Hide amount' : 'Show amount'" :aria-pressed="shown" @click.stop.prevent="shown = !shown">
		{{ shown ? formatMoney(amount, currency || "INR") : masked }}
		<component :is="shown ? EyeOff : Eye" class="h-4 w-4 text-ink-400" />
	</button>
</template>
