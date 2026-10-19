<script setup lang="ts">
import { ShieldCheck } from "lucide-vue-next"
import { ref, watch } from "vue"

import { call } from "@/api/client"
import type { SalarySlipList } from "@/api/types"
import AppBar from "@/components/ui/AppBar.vue"
import EmptyState from "@/components/ui/EmptyState.vue"
import ErrorState from "@/components/ui/ErrorState.vue"
import MaskedAmount from "@/components/ui/MaskedAmount.vue"
import Pagination from "@/components/ui/Pagination.vue"
import Skeleton from "@/components/ui/Skeleton.vue"
import { useResource } from "@/composables/useResource"
import { formatDate, formatMoney, monthLabel, titleCase } from "@/lib/format"

const props = defineProps<{ employee?: string }>()
const year = ref<number | "">("")
const page = ref(1)
const pageLength = 12

const { data, error, loading, reload } = useResource((signal) =>
	call<SalarySlipList>("salary.get_salary_slips", { employee: props.employee, year: year.value, page: page.value, page_length: pageLength }, { signal }),
)
watch(year, () => (page.value === 1 ? reload() : (page.value = 1)))
watch(page, () => reload())
</script>

<template>
	<div>
		<AppBar :title="employee ? titleCase(data?.employee_name) || 'Salary Slip' : 'Salary Slip'" :subtitle="employee ? 'HR view' : undefined" :back="employee ? '/directory' : '/'" />

		<div v-if="data?.years.length" class="mb-3 flex items-center justify-between">
			<label class="relative">
				<span class="sr-only">Year</span>
				<select v-model="year" class="h-10 rounded-[10px] border border-ink-200 bg-white pl-3 pr-8 text-[14px]"><option value="">All years</option><option v-for="y in data.years" :key="y" :value="y">{{ y }}</option></select>
			</label>
			<span class="text-[13px] text-ink-500">{{ data.total }} slip{{ data.total === 1 ? "" : "s" }}</span>
		</div>

		<ErrorState v-if="error" :error="error" :retrying="loading" @retry="reload" />
		<div v-else-if="!data" class="space-y-2.5"><Skeleton v-for="i in 3" :key="i" card :lines="3" /></div>
		<template v-else>
			<div class="space-y-2.5" :class="loading ? 'opacity-60' : ''">
				<RouterLink v-for="s in data.rows" :key="s.name" :to="`/salary/${encodeURIComponent(s.name)}`" class="card block p-3.5">
					<div class="flex items-center justify-between">
						<p class="text-[15px] font-medium">{{ monthLabel(s.start_date) }}</p>
						<span class="inline-flex items-center gap-1 text-[14px] font-medium text-success">Submitted<span class="h-2 w-2 rounded-full bg-success" /></span>
					</div>
					<div class="mt-2 flex items-center justify-between">
						<p class="text-[13px] text-ink-500">{{ formatDate(s.start_date, { year: false }) }} – {{ formatDate(s.end_date) }}</p>
						<MaskedAmount class="text-lg" :amount="s.rounded_total || s.net_pay" :currency="s.currency" />
					</div>
					<p class="mt-1 text-[13px] text-ink-500">Gross {{ formatMoney(s.gross_pay, s.currency) }} · <span class="text-danger">- {{ formatMoney(s.total_deduction, s.currency) }}</span></p>
				</RouterLink>
				<div v-if="!data.rows.length" class="card"><EmptyState description="Slips appear here once HR submits payroll for a month." /></div>
			</div>
			<Pagination v-model="page" :total="data.total" :page-length="pageLength" />
			<p class="mt-4 flex items-center justify-center gap-1.5 text-xs text-ink-400"><ShieldCheck class="h-3.5 w-3.5" /> Only you and HR can see these. Payslips are never stored offline.</p>
		</template>
	</div>
</template>
