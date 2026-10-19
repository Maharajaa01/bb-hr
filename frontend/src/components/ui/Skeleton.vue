<script setup lang="ts">
defineProps<{ lines?: number; card?: boolean }>()
</script>

<template>
	<div :class="card ? 'card p-4' : ''" aria-busy="true" aria-label="Loading">
		<div class="space-y-3">
			<div v-for="i in lines ?? 3" :key="i" class="relative h-4 overflow-hidden rounded-md bg-ink-100" :style="{ width: `${100 - ((i * 17) % 45)}%` }">
				<div class="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/70 to-transparent" />
			</div>
		</div>
	</div>
</template>
