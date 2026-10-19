<script setup lang="ts">
import Spot, { type SpotName } from "@/components/illustrations/Spot.vue"

defineProps<{ to: string; label: string; spot: SpotName }>()
</script>

<template>
	<RouterLink :to="to" class="flex aspect-[4/5] flex-col items-center justify-between gap-1 rounded-xl border border-ink-200 bg-white px-1.5 pb-2.5 pt-2 text-center transition hover:border-brand-300 active:scale-[.98]">
		<Spot :name="spot" class="h-[84px] w-full" />
		<span class="line-clamp-2 text-[14px] leading-tight text-ink-900">{{ label }}</span>
	</RouterLink>
</template>
