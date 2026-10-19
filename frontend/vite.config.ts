import { fileURLToPath, URL } from "node:url"

import vue from "@vitejs/plugin-vue"
import { defineConfig } from "vite"

const APP = "bb_academy_hrms"

export default defineConfig({
	plugins: [vue()],
	base: `/assets/${APP}/bbhr/`,
	resolve: {
		alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
	},
	build: {
		outDir: `../${APP}/public/bbhr`,
		emptyOutDir: true,
		target: "es2019",
		sourcemap: false,
		rollupOptions: {
			output: {
				entryFileNames: "assets/[name].[hash].js",
				chunkFileNames: "assets/[name].[hash].js",
				assetFileNames: "assets/[name].[hash].[ext]",
			},
		},
	},
	server: {
		port: 8081,
		proxy: {
			"^/(api|assets|files|private|bbhr_sw.js)": {
				target: process.env.BBHR_BACKEND || "http://localhost:8000",
				changeOrigin: true,
			},
		},
	},
})
