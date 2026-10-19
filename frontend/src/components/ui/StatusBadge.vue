<script setup lang="ts">
import { computed } from "vue"

import Badge from "./Badge.vue"

/** StatusChip: Pending/leave = orange, Approved/present = green, Rejected/absent = red, Holiday = blue. */
const props = defineProps<{ status: string }>()
const tone = computed(() => {
	switch (props.status) {
		case "Present":
		case "Work From Home":
		case "In Now":
		case "Approved":
		case "Paid":
		case "Submitted":
			return "success"
		case "Half Day":
		case "Late":
		case "Late Arrival":
		case "Missing Check-out":
		case "On Leave":
		case "Pending":
			return "warning"
		case "Absent":
		case "Not Marked":
		case "Rejected":
			return "danger"
		case "Holiday":
			return "info"
		default:
			return "neutral"
	}
})
</script>

<template>
	<Badge :tone="tone">{{ status }}</Badge>
</template>
