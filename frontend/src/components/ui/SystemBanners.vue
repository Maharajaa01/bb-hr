<script setup lang="ts">
import { useOnline } from "@vueuse/core"
import { RefreshCw, WifiOff } from "lucide-vue-next"

import { applyUpdate, updateReady } from "@/lib/pwa"

const online = useOnline()
</script>

<template>
	<div>
		<div v-if="!online" class="flex items-center justify-center gap-2 bg-ink-900 px-4 py-2 text-center text-sm font-medium text-white" role="status">
			<WifiOff class="h-4 w-4 text-brand-200" />
			You're offline. Check-in, payslips and live data need a connection.
		</div>
		<div v-if="updateReady" class="flex items-center justify-center gap-3 bg-brand-50 px-4 py-2 text-sm text-brand-700" role="status">
			A new version of BB HRMS is ready.
			<button class="inline-flex items-center gap-1 font-semibold underline" @click="applyUpdate"><RefreshCw class="h-3.5 w-3.5" /> Update</button>
		</div>
	</div>
</template>
