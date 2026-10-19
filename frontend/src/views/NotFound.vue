<script setup lang="ts">
import { Compass } from "lucide-vue-next"

import AppButton from "@/components/ui/AppButton.vue"
import AppBar from "@/components/ui/AppBar.vue"
import EmptyState from "@/components/ui/EmptyState.vue"
</script>

<template>
	<div>
		<AppBar title="Not found" />
		<div class="card">
			<EmptyState :icon="Compass" title="Page not found" description="The link may be old or mistyped.">
				<AppButton to="/" variant="secondary">Go home</AppButton>
			</EmptyState>
		</div>
	</div>
</template>
