<!-- BB HRMS mark: same as the app icon (scripts/make_icons.py) - blue tile, bold "BB" over "HRMS". -->
<template>
	<div class="flex items-center gap-3">
		<svg viewBox="0 0 64 64" class="h-14 w-14" aria-hidden="true">
			<defs>
				<linearGradient id="bb-mark" x1="0" y1="0" x2="0" y2="1">
					<stop offset="0" stop-color="#1A9CFF" />
					<stop offset="1" stop-color="#0378E6" />
				</linearGradient>
			</defs>
			<rect width="64" height="64" rx="14.4" fill="url(#bb-mark)" />
			<text x="32" y="36" text-anchor="middle" font-family="Poppins, -apple-system, system-ui, Segoe UI, Arial, sans-serif" font-size="26" font-weight="900" letter-spacing="-0.5" fill="#fff">BB</text>
			<text x="32" y="50" text-anchor="middle" font-family="Poppins, -apple-system, system-ui, Segoe UI, Arial, sans-serif" font-size="10" font-weight="800" letter-spacing="1.8" fill="#fff">HRMS</text>
		</svg>
		<div>
			<p class="text-[22px] font-bold leading-none text-ink-900">BB <span class="text-brand-500">HRMS</span></p>
			<p class="mt-1 text-[12px] text-ink-500">Black Building Academy</p>
		</div>
	</div>
</template>
