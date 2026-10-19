<script setup lang="ts">
import { computed, ref } from "vue"

/** Photo, or a yellow circle with the white initial. */
const props = withDefaults(defineProps<{ name?: string | null; image?: string | null; size?: "sm" | "md" | "lg" | "xl"; square?: boolean }>(), { size: "md" })
const failed = ref(false)
const initial = computed(() => {
	const words = (props.name || "?").trim().split(/\s+/)
	const word = words.find((w) => w.length > 1) || words[0] || "?"
	return word[0].toUpperCase()
})
const sizeClass = computed(() => ({ sm: "h-8 w-8 text-sm", md: "h-10 w-10 text-base", lg: "h-14 w-14 text-xl", xl: "h-20 w-20 text-3xl" })[props.size])
const shape = computed(() => (props.square ? "rounded-2xl" : "rounded-full"))
</script>

<template>
	<img v-if="image && !failed" :src="image" :alt="name ?? ''" class="shrink-0 object-cover" :class="[sizeClass, shape]" @error="failed = true" />
	<span v-else class="grid shrink-0 place-items-center bg-avatar font-semibold text-white" :class="[sizeClass, shape]" aria-hidden="true">{{ initial }}</span>
</template>
