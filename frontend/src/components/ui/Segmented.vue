<script setup lang="ts" generic="T extends string">
defineProps<{ options: { value: T; label: string }[]; label?: string }>()
const model = defineModel<T>({ required: true })
</script>

<template>
	<div class="inline-flex rounded-xl bg-brand-100 p-1" role="radiogroup" :aria-label="label">
		<button
			v-for="o in options"
			:key="o.value"
			type="button"
			role="radio"
			:aria-checked="model === o.value"
			class="rounded-lg px-3 py-1.5 text-sm font-semibold transition"
			:class="model === o.value ? 'bg-white text-brand-700 shadow-sm' : 'text-ink-500 hover:text-brand-700'"
			@click="model = o.value"
		>
			{{ o.label }}
		</button>
	</div>
</template>
