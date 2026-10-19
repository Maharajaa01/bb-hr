<script setup lang="ts">
defineProps<{ label: string; active?: boolean }>()
</script>

<template>
	<button type="button" class="grid h-10 w-10 place-items-center rounded-[10px] border bg-white transition" :class="active ? 'border-brand-500 text-brand-500' : 'border-ink-200 text-ink-700 hover:bg-ink-50'" :aria-label="label" :aria-pressed="active">
		<slot />
	</button>
</template>
