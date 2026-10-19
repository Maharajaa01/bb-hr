<script setup lang="ts">
import { AlertTriangle, Lock, RefreshCw, WifiOff } from "lucide-vue-next"
import { computed } from "vue"

import type { ApiError } from "@/api/client"

import AppButton from "./AppButton.vue"

const props = defineProps<{ error: ApiError; retrying?: boolean }>()
const emit = defineEmits<{ retry: [] }>()

const icon = computed(() => (props.error.isNetwork ? WifiOff : props.error.isPermission ? Lock : AlertTriangle))
const title = computed(() =>
	props.error.isNetwork ? "You're offline" : props.error.isPermission ? "Not allowed" : props.error.title || "Couldn't load this",
)
</script>

<template>
	<div class="card flex flex-col items-center px-6 py-10 text-center" role="alert">
		<div class="mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-danger-soft text-danger">
			<component :is="icon" class="h-6 w-6" />
		</div>
		<p class="font-semibold text-ink-800">{{ title }}</p>
		<p class="mt-1 max-w-sm text-sm text-ink-500">{{ error.message }}</p>
		<AppButton v-if="!error.isPermission" class="mt-4" variant="secondary" size="sm" :loading="retrying" @click="emit('retry')">
			<RefreshCw class="h-4 w-4" /> Try again
		</AppButton>
	</div>
</template>
