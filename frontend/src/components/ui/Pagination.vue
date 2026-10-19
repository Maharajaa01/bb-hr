<script setup lang="ts">
import { ChevronLeft, ChevronRight } from "lucide-vue-next"
import { computed } from "vue"

const props = defineProps<{ total: number; pageLength: number }>()
const page = defineModel<number>({ required: true })
const pages = computed(() => Math.max(1, Math.ceil(props.total / props.pageLength)))
const from = computed(() => (props.total ? (page.value - 1) * props.pageLength + 1 : 0))
const to = computed(() => Math.min(props.total, page.value * props.pageLength))
</script>

<template>
	<nav v-if="total > pageLength" class="mt-4 flex items-center justify-between text-sm text-ink-600" aria-label="Pagination">
		<span class="tabular">{{ from }}–{{ to }} of {{ total }}</span>
		<div class="flex gap-2">
			<button class="grid h-9 w-9 place-items-center rounded-xl border border-ink-200 bg-white disabled:opacity-40" :disabled="page <= 1" aria-label="Previous page" @click="page--">
				<ChevronLeft class="h-4 w-4" />
			</button>
			<button class="grid h-9 w-9 place-items-center rounded-xl border border-ink-200 bg-white disabled:opacity-40" :disabled="page >= pages" aria-label="Next page" @click="page++">
				<ChevronRight class="h-4 w-4" />
			</button>
		</div>
	</nav>
</template>
