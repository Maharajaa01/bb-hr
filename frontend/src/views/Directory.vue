<script setup lang="ts">
import { useDebounceFn } from "@vueuse/core"
import { CalendarRange, IndianRupee, Mail, Phone, Search } from "lucide-vue-next"
import { ref, watch } from "vue"

import { call } from "@/api/client"
import type { Directory } from "@/api/types"
import AppBar from "@/components/ui/AppBar.vue"
import Avatar from "@/components/ui/Avatar.vue"
import EmptyState from "@/components/ui/EmptyState.vue"
import ErrorState from "@/components/ui/ErrorState.vue"
import Pagination from "@/components/ui/Pagination.vue"
import Skeleton from "@/components/ui/Skeleton.vue"
import { useResource } from "@/composables/useResource"
import { titleCase } from "@/lib/format"
import { useSession } from "@/stores/session"

const session = useSession()
const search = ref("")
const department = ref("")
const page = ref(1)
const pageLength = 30

const departments = useResource((signal) => call<string[]>("team.get_departments", {}, { signal }))
const { data, error, loading, reload } = useResource((signal) =>
	call<Directory>("team.get_directory", { search: search.value, department: department.value, page: page.value, page_length: pageLength }, { signal }),
)
const debounced = useDebounceFn(() => (page.value === 1 ? reload() : (page.value = 1)), 300)
watch(search, debounced)
watch(department, () => (page.value === 1 ? reload() : (page.value = 1)))
watch(page, () => reload())
</script>

<template>
	<div>
		<AppBar title="Directory" :subtitle="data ? `${data.total} ${session.isHr ? 'active employees' : 'in your team'}` : undefined" />
		<label class="relative mb-2 block"><span class="sr-only">Search</span>
			<Search class="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-400" />
			<input v-model="search" type="search" class="field rounded-full pl-11" placeholder="Search name, ID or designation" />
		</label>
		<label v-if="departments.data.value?.length" class="mb-3 block"><span class="sr-only">Department</span>
			<select v-model="department" class="field"><option value="">All departments</option><option v-for="d in departments.data.value" :key="d" :value="d">{{ d }}</option></select>
		</label>

		<ErrorState v-if="error" :error="error" :retrying="loading" @retry="reload" />
		<Skeleton v-else-if="!data" card :lines="8" />
		<template v-else>
			<div class="divide-y divide-ink-200 border-y border-ink-200" :class="loading ? 'opacity-60' : ''">
				<div v-for="e in data.rows" :key="e.name" class="flex items-center gap-3 py-3">
					<Avatar :name="e.employee_name" :image="e.image" />
					<div class="min-w-0 flex-1">
						<RouterLink :to="`/team/${e.name}`" class="block">
							<p class="truncate font-medium">{{ titleCase(e.employee_name) }}</p>
							<p class="truncate text-[13px] text-ink-500">{{ titleCase(e.designation) || "—" }} · {{ e.name }}</p>
						</RouterLink>
						<p v-if="data.is_hr" class="mt-0.5 flex items-center gap-2 text-[12px]">
							<span v-if="!e.has_login" class="text-warning-deep">No login</span>
							<RouterLink :to="`/hr/salary/${e.name}`" class="inline-flex items-center gap-0.5 text-brand-500"><IndianRupee class="h-3 w-3" />Salary slips</RouterLink>
						</p>
					</div>
					<div class="flex shrink-0 gap-1.5">
						<a v-if="e.cell_number" :href="`tel:${e.cell_number}`" class="grid h-10 w-10 place-items-center rounded-full bg-brand-50 text-brand-500" :aria-label="`Call ${e.employee_name}`"><Phone class="h-[18px] w-[18px]" /></a>
						<a v-if="e.company_email" :href="`mailto:${e.company_email}`" class="grid h-10 w-10 place-items-center rounded-full bg-brand-50 text-brand-500" :aria-label="`Email ${e.employee_name}`"><Mail class="h-[18px] w-[18px]" /></a>
						<RouterLink v-if="!e.cell_number && !e.company_email" :to="`/team/${e.name}`" class="grid h-10 w-10 place-items-center rounded-full bg-brand-50 text-brand-500" :aria-label="`Attendance of ${e.employee_name}`"><CalendarRange class="h-[18px] w-[18px]" /></RouterLink>
					</div>
				</div>
			</div>
			<div v-if="!data.rows.length" class="card"><EmptyState spot="directory" :description="search ? 'Try another name or ID.' : 'No employees in your scope yet.'" /></div>
			<Pagination v-model="page" :total="data.total" :page-length="pageLength" />
		</template>
	</div>
</template>
