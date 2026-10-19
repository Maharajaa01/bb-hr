<script setup lang="ts">
import { AlertTriangle, CheckCircle2, Info, X, XCircle } from "lucide-vue-next"

import { useToasts } from "@/stores/toast"

const toasts = useToasts()
const icons = { success: CheckCircle2, error: XCircle, info: Info, warning: AlertTriangle }
</script>

<template>
	<div class="pointer-events-none fixed inset-x-0 bottom-20 z-50 mx-auto flex max-w-app flex-col items-center gap-2 p-3 safe-bottom" aria-live="polite">
		<TransitionGroup name="fade">
			<div v-for="t in toasts.items" :key="t.id" class="pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-xl bg-ink-900 p-3.5 text-white shadow-lift" role="status">
				<component
					:is="icons[t.tone]"
					class="mt-0.5 h-5 w-5 shrink-0"
					:class="{ success: 'text-success', error: 'text-danger', info: 'text-brand-300', warning: 'text-warning' }[t.tone]"
				/>
				<div class="min-w-0 flex-1">
					<p class="text-sm font-semibold">{{ t.title }}</p>
					<p v-if="t.message" class="mt-0.5 text-sm text-ink-300">{{ t.message }}</p>
				</div>
				<button class="-m-1 rounded-lg p-1 text-ink-400 hover:text-white" aria-label="Dismiss" @click="toasts.dismiss(t.id)"><X class="h-4 w-4" /></button>
			</div>
		</TransitionGroup>
	</div>
</template>
