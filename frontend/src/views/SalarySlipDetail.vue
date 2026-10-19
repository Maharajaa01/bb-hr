<script setup lang="ts">
import { Download } from "lucide-vue-next"
import { computed } from "vue"

import { call, fileUrl } from "@/api/client"
import type { SalarySlipDetail } from "@/api/types"
import AppBar from "@/components/ui/AppBar.vue"
import AppButton from "@/components/ui/AppButton.vue"
import ErrorState from "@/components/ui/ErrorState.vue"
import Skeleton from "@/components/ui/Skeleton.vue"
import { useResource } from "@/composables/useResource"
import { formatDate, formatMoney, monthLabel, titleCase } from "@/lib/format"

const props = defineProps<{ name: string }>()
const slipName = computed(() => decodeURIComponent(props.name))
const { data, error, loading, reload } = useResource((signal) => call<SalarySlipDetail>("salary.get_salary_slip", { name: slipName.value }, { signal }))
const pdf = computed(() => fileUrl("salary.download_salary_slip", { name: slipName.value }))
</script>

<template>
	<div>
		<AppBar :title="data ? monthLabel(data.start_date) : 'Payslip'" :subtitle="data ? `${titleCase(data.employee_name)} · ${data.employee}` : undefined" back />

		<ErrorState v-if="error" :error="error" :retrying="loading" @retry="reload" />
		<Skeleton v-else-if="!data" card :lines="10" />
		<div v-else class="space-y-3">
			<section class="relative overflow-hidden rounded-xl border border-ink-200 bg-gradient-to-br from-white to-brand-50 p-4">
				<span class="absolute -right-8 -top-8 h-24 w-24 rounded-full bg-brand-100" aria-hidden="true" />
				<p class="relative text-[13px] text-ink-500">Net Pay</p>
				<p class="tabular relative mt-0.5 text-3xl font-semibold text-brand-600">{{ formatMoney(data.rounded_total || data.net_pay, data.currency) }}</p>
				<p v-if="data.total_in_words" class="relative mt-1 text-[13px] text-ink-500">{{ data.total_in_words }}</p>
				<dl class="relative mt-4 grid grid-cols-3 gap-2 text-[13px]">
					<div><dt class="text-ink-500">Working days</dt><dd class="tabular font-medium">{{ data.total_working_days }}</dd></div>
					<div><dt class="text-ink-500">Payment days</dt><dd class="tabular font-medium">{{ data.payment_days }}</dd></div>
					<div><dt class="text-ink-500">Absent / LWP</dt><dd class="tabular font-medium">{{ data.absent_days }} / {{ data.leave_without_pay }}</dd></div>
					<div class="col-span-3"><dt class="text-ink-500">Period</dt><dd class="font-medium">{{ formatDate(data.start_date) }} – {{ formatDate(data.end_date) }}</dd></div>
					<div v-if="data.bank_name || data.bank_account_no" class="col-span-3"><dt class="text-ink-500">Bank</dt><dd class="font-medium">{{ [data.bank_name, data.bank_account_no].filter(Boolean).join(" · ") }}</dd></div>
				</dl>
			</section>

			<section v-for="block in [{ title: 'Earnings', lines: data.earnings, total: data.gross_pay, totalLabel: 'Gross Pay' }, { title: 'Deductions', lines: data.deductions, total: data.total_deduction, totalLabel: 'Total Deductions' }]" :key="block.title" class="-mx-3">
				<table class="w-full text-[14px]">
					<thead><tr class="bg-ink-100 text-left text-ink-700"><th class="px-3 py-2.5 font-medium">{{ block.title }}</th><th class="px-3 py-2.5 text-right font-medium">Amount</th></tr></thead>
					<tbody class="tabular">
						<tr v-for="l in block.lines" :key="l.component" class="border-b border-ink-200"><td class="px-3 py-2.5">{{ l.component }}</td><td class="px-3 py-2.5 text-right">{{ formatMoney(l.amount, data.currency) }}</td></tr>
						<tr v-if="!block.lines.length" class="border-b border-ink-200"><td colspan="2" class="px-3 py-2.5 text-ink-500">None</td></tr>
						<tr class="font-semibold"><td class="px-3 py-2.5">{{ block.totalLabel }}</td><td class="px-3 py-2.5 text-right" :class="block.title === 'Deductions' ? 'text-danger' : ''">{{ formatMoney(block.total, data.currency) }}</td></tr>
					</tbody>
				</table>
			</section>

			<AppButton :href="pdf" block><Download class="h-5 w-5" /> Download PDF</AppButton>
		</div>
	</div>
</template>
