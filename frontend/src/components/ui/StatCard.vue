<script setup lang="ts">
import { CalendarDays } from "lucide-vue-next"
import type { Component } from "vue"

/** Leave-balance style card: tinted icon, big coloured number, label, decorative blurred circle. */
withDefaults(defineProps<{ label: string; value: string | number; tone?: "lavender" | "peach" | "mint" | "blue"; icon?: Component }>(), { tone: "blue" })
</script>

<template>
	<div class="relative min-w-[140px] flex-1 overflow-hidden rounded-xl border border-ink-200 bg-white p-3.5">
		<span
			class="absolute -bottom-6 -right-6 h-20 w-20 rounded-full blur-xl"
			:class="{ lavender: 'bg-lavender', peach: 'bg-warning-soft', mint: 'bg-success-soft', blue: 'bg-brand-100' }[tone]"
			aria-hidden="true"
		/>
		<div class="relative flex items-start justify-between">
			<span class="grid h-9 w-9 place-items-center rounded-lg" :class="{ lavender: 'bg-lavender text-lavender-deep', peach: 'bg-warning-soft text-warning-deep', mint: 'bg-success-soft text-success', blue: 'bg-brand-50 text-brand-500' }[tone]">
				<component :is="icon ?? CalendarDays" class="h-5 w-5" :stroke-width="1.7" />
			</span>
			<span class="tabular whitespace-nowrap pl-2 text-2xl font-semibold" :class="{ lavender: 'text-lavender-deep', peach: 'text-warning-deep', mint: 'text-success', blue: 'text-brand-500' }[tone]">{{ value }}</span>
		</div>
		<p class="relative mt-3 text-[14px] text-ink-700">{{ label }}</p>
	</div>
</template>
