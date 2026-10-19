<script setup lang="ts">
import { useRoute } from "vue-router"

/** Tabs inside the blue header; active tab gets a lime underline. */
defineProps<{ tabs: { to: string; label: string }[] }>()
const route = useRoute()
</script>

<template>
	<nav class="flex gap-6 px-4" aria-label="Sections">
		<RouterLink
			v-for="t in tabs"
			:key="t.to"
			:to="t.to"
			class="relative flex h-11 items-center text-[16px]"
			:class="route.path === t.to ? 'font-medium text-white' : 'text-white/80 hover:text-white'"
			:aria-current="route.path === t.to ? 'page' : undefined"
		>
			{{ t.label }}
			<span v-if="route.path === t.to" class="absolute inset-x-0 bottom-0 h-[3px] rounded-full bg-lime" aria-hidden="true" />
		</RouterLink>
	</nav>
</template>
