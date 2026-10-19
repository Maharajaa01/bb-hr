<script setup lang="ts">
import type { Component } from "vue"

import Spot, { type SpotName } from "@/components/illustrations/Spot.vue"

defineProps<{ icon?: Component; spot?: SpotName; title?: string; description?: string }>()
</script>

<template>
	<div class="flex flex-col items-center px-6 py-10 text-center">
		<Spot :name="spot ?? 'empty'" class="mb-3 h-28 w-40" />
		<p class="font-semibold text-ink-900">{{ title ?? "No Detail found" }}</p>
		<p v-if="description" class="mt-1 max-w-xs text-[13px] text-ink-500">{{ description }}</p>
		<div v-if="$slots.default" class="mt-4"><slot /></div>
	</div>
</template>
