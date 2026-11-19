<script setup lang="ts">
import BottomNav from "@/components/ui/BottomNav.vue"
import DesktopSidebar from "@/components/ui/DesktopSidebar.vue"
import FabActionSheet from "@/components/ui/FabActionSheet.vue"
import SideDrawer from "@/components/ui/SideDrawer.vue"
import SystemBanners from "@/components/ui/SystemBanners.vue"
</script>

<!--
	Phones (and anything under 1024px): a 480px app frame with the blue top bar, bottom tabs and drawer.
	Desktop: a fixed sidebar and a centred content column up to 72rem; pages add their own lg: layouts.
-->
<template>
	<div class="min-h-screen lg:bg-ink-50">
		<DesktopSidebar />
		<div class="relative mx-auto min-h-screen max-w-app bg-white sm:shadow-lift lg:ml-64 lg:max-w-none lg:bg-transparent lg:shadow-none">
			<SystemBanners />
			<main class="px-3 pb-28 lg:px-8 lg:pb-12">
				<div class="lg:mx-auto lg:max-w-6xl">
					<RouterView v-slot="{ Component }">
						<Transition name="slide" mode="out-in">
							<component :is="Component" :key="$route.fullPath" />
						</Transition>
					</RouterView>
				</div>
			</main>
		</div>
		<BottomNav />
		<SideDrawer />
		<FabActionSheet />
	</div>
</template>
