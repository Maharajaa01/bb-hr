<script setup lang="ts">
import type { Component } from "vue"

defineProps<{
	label: string
	value: string | number
	hint?: string
	icon?: Component
	tone?: "neutral" | "success" | "warning" | "danger" | "info" | "gold"
	active?: boolean
	clickable?: boolean
}>()
</script>

<template>
	<component
		:is="clickable ? 'button' : 'div'"
		class="card flex min-w-0 flex-col p-3 text-left transition"
		:class="[clickable ? 'hover:border-brand-300' : '', active ? 'border-brand-500 ring-1 ring-brand-500' : '']"
		:type="clickable ? 'button' : undefined"
		:aria-pressed="clickable ? !!active : undefined"
	>
		<div class="flex items-center gap-2 text-[13px] text-ink-500">
			<span
				v-if="icon"
				class="grid h-6 w-6 place-items-center rounded-lg"
				:class="{
					neutral: 'bg-ink-100 text-ink-600',
					success: 'bg-success-soft text-success',
					warning: 'bg-warning-soft text-warning-deep',
					danger: 'bg-danger-soft text-danger',
					info: 'bg-lavender text-lavender-deep',
					gold: 'bg-brand-50 text-brand-500',
				}[tone ?? 'neutral']"
			>
				<component :is="icon" class="h-3.5 w-3.5" />
			</span>
			<span class="truncate">{{ label }}</span>
		</div>
		<div class="tabular mt-1.5 text-2xl font-semibold text-ink-900">{{ value }}</div>
		<div v-if="hint" class="mt-0.5 truncate text-xs text-ink-500">{{ hint }}</div>
	</component>
</template>
