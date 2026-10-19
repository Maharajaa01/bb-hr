<script setup lang="ts">
import { computed } from "vue"

import Spinner from "./Spinner.vue"

/** PrimaryButton and friends: 48px, 12px radius. */
const props = withDefaults(
	defineProps<{
		variant?: "primary" | "accent" | "secondary" | "ghost" | "danger"
		size?: "sm" | "md" | "lg"
		loading?: boolean
		disabled?: boolean
		block?: boolean
		type?: "button" | "submit"
		to?: string | Record<string, unknown>
		href?: string
	}>(),
	{ variant: "primary", size: "md", type: "button" },
)

const classes = computed(() => [
	"inline-flex select-none items-center justify-center gap-2 rounded-xl font-medium transition active:scale-[.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:active:scale-100",
	{
		primary: "bg-brand-500 text-white hover:bg-brand-600 active:bg-brand-600",
		accent: "bg-brand-500 text-white hover:bg-brand-600 active:bg-brand-600",
		secondary: "border border-ink-200 bg-white text-brand-600 hover:bg-brand-50",
		ghost: "text-brand-600 hover:bg-brand-50",
		danger: "bg-danger text-white hover:bg-danger-dark",
	}[props.variant],
	{ sm: "h-9 px-3 text-sm", md: "h-12 px-4 text-[15px]", lg: "h-12 px-6 text-base" }[props.size],
	props.block ? "w-full" : "",
])
</script>

<template>
	<RouterLink v-if="to && !disabled" :to="to" :class="classes"><slot /></RouterLink>
	<a v-else-if="href && !disabled" :href="href" :class="classes"><slot /></a>
	<button v-else :type="type" :class="classes" :disabled="disabled || loading" :aria-busy="loading">
		<Spinner v-if="loading" class="h-4 w-4" />
		<slot />
	</button>
</template>
