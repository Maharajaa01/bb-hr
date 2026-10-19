<script setup lang="ts">
import { Lock } from "lucide-vue-next"

import AppButton from "@/components/ui/AppButton.vue"
import AppBar from "@/components/ui/AppBar.vue"
import EmptyState from "@/components/ui/EmptyState.vue"
</script>

<template>
	<div>
		<AppBar title="Not allowed" />
		<div class="card">
			<EmptyState :icon="Lock" title="You don't have access to this page" description="It's for reporting managers or HR. If you think you should see it, ask HR to check your role.">
				<AppButton to="/" variant="secondary">Go home</AppButton>
			</EmptyState>
		</div>
	</div>
</template>
