<!--
  unDraw illustrations recoloured to brand blue (see src/assets/illustrations/README.md).
  Imported as URLs so Vite gives each file a content hash: nginx caches /assets for a year,
  so a changed illustration must get a new file name or phones keep showing the old one.
  Loaded as <img> so they stay out of the JS bundle and can never execute script.
-->
<script setup lang="ts">
import { computed } from "vue"

export type SpotName =
	| "checkin" | "attendance" | "salary" | "holiday" | "directory" | "team" | "alert" | "chart" | "profile" | "empty" | "leave" | "login"
const props = defineProps<{ name: SpotName; alt?: string }>()
const urls = import.meta.glob<string>("../../assets/illustrations/*.svg", { eager: true, query: "?url", import: "default" })
const src = computed(() => urls[`../../assets/illustrations/${props.name}.svg`])
</script>

<template>
	<img :src="src" :alt="alt ?? ''" class="block object-contain" loading="lazy" decoding="async" draggable="false" />
</template>
