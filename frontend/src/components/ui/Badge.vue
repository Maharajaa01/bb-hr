<script setup lang="ts">
withDefaults(defineProps<{ tone?: "neutral" | "success" | "warning" | "danger" | "info" | "gold" }>(), { tone: "neutral" })
</script>

<template>
	<span
		class="inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium"
		:class="{
			neutral: 'bg-ink-100 text-ink-700',
			success: 'bg-success-soft text-success',
			warning: 'bg-warning-soft text-warning-deep',
			danger: 'bg-danger-soft text-danger',
			info: 'bg-brand-50 text-brand-600',
			gold: 'bg-brand-50 text-brand-600',
		}[tone]"
	>
		<slot />
	</span>
</template>
