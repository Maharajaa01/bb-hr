<script setup lang="ts">
import BottomNav from "@/components/ui/BottomNav.vue"
import FabActionSheet from "@/components/ui/FabActionSheet.vue"
import SideDrawer from "@/components/ui/SideDrawer.vue"
import SystemBanners from "@/components/ui/SystemBanners.vue"
</script>

<template>
	<div class="relative mx-auto min-h-screen max-w-app bg-white sm:shadow-lift">
		<SystemBanners />
		<main class="px-3 pb-28">
			<RouterView v-slot="{ Component }">
				<Transition name="slide" mode="out-in">
					<component :is="Component" :key="$route.fullPath" />
				</Transition>
			</RouterView>
		</main>
		<BottomNav />
		<SideDrawer />
		<FabActionSheet />
	</div>
</template>
