<script setup lang="ts">
import { ArrowLeft, Menu } from "lucide-vue-next"
import { computed } from "vue"
import { useRouter } from "vue-router"

import { useUi } from "@/stores/ui"

/** Solid blue top bar. `back` shows a back arrow, otherwise the drawer hamburger. The `extension` slot continues the blue header below the bar. */
const props = defineProps<{ title: string; subtitle?: string; back?: string | boolean }>()
const router = useRouter()
const ui = useUi()

// a bare `back` attribute arrives as "" (String is checked before Boolean), so treat "" as true
const hasBack = computed(() => props.back !== undefined && props.back !== false)

function goBack() {
	if (typeof props.back === "string" && props.back) router.push(props.back)
	else if (window.history.state?.back) router.back()
	else router.push("/")
}
</script>

<template>
	<header class="sticky top-0 z-20 -mx-3 mb-3 bg-brand-500 text-white safe-top">
		<div class="flex h-14 items-center gap-1 px-1">
			<button v-if="hasBack" class="grid h-11 w-11 shrink-0 place-items-center rounded-full hover:bg-white/15" aria-label="Back" @click="goBack">
				<ArrowLeft class="h-6 w-6" />
			</button>
			<button v-else class="grid h-11 w-11 shrink-0 place-items-center rounded-full hover:bg-white/15" aria-label="Open menu" aria-haspopup="dialog" @click="ui.drawerOpen = true">
				<Menu class="h-6 w-6" />
			</button>
			<div class="min-w-0 flex-1 pl-1">
				<h1 class="truncate text-[19px] font-medium leading-tight">{{ title }}</h1>
				<p v-if="subtitle" class="truncate text-[12px] leading-tight text-white/85">{{ subtitle }}</p>
			</div>
			<div v-if="$slots.actions" class="flex shrink-0 items-center gap-1 pr-2"><slot name="actions" /></div>
		</div>
		<slot name="extension" />
	</header>
</template>
