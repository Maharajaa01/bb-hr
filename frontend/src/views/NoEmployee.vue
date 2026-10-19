<script setup lang="ts">
import { UserX } from "lucide-vue-next"

import AppButton from "@/components/ui/AppButton.vue"
import AppBar from "@/components/ui/AppBar.vue"
import EmptyState from "@/components/ui/EmptyState.vue"
import { useSession } from "@/stores/session"

const session = useSession()
</script>

<template>
	<div>
		<AppBar title="Account" />
		<div class="card">
			<EmptyState
				:icon="UserX"
				title="Your login isn't linked to an employee"
				:description="session.employee && session.employee.status !== 'Active'
					? `Your employee record is ${session.employee.status}. Ask HR if this is a mistake.`
					: `Ask HR to set ${session.user?.name} as the User on your Employee record, then sign in again.`"
			>
				<div class="flex flex-wrap justify-center gap-2">
					<AppButton v-if="session.hasTeamAccess" to="/team" variant="secondary">Open team view</AppButton>
					<AppButton variant="ghost" @click="session.logout()">Sign out</AppButton>
				</div>
			</EmptyState>
		</div>
	</div>
</template>
