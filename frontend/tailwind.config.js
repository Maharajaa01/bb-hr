/**
 * BB HR design tokens (see docs/BBHR.md "Design system").
 * brand = primary blue #048EFF, ink = neutral text/greys, plus semantic danger/success/warning
 * and the tints used by the leave-balance cards.
 */
/** @type {import('tailwindcss').Config} */
export default {
	content: ["./index.html", "./src/**/*.{vue,ts}"],
	theme: {
		extend: {
			colors: {
				brand: {
					50: "#EAF5FF", 100: "#D3EAFF", 200: "#A8D5FF", 300: "#6DBAFF", 400: "#36A2FF",
					500: "#048EFF", 600: "#0277D6", 700: "#0261AF", 800: "#034C88", 900: "#063B68",
				},
				ink: {
					50: "#F7F7F7", 100: "#F1F1F1", 200: "#E3E3E3", 300: "#CFCFCF", 400: "#A6A6A6",
					500: "#808080", 600: "#666666", 700: "#4A4A4A", 800: "#333333", 900: "#212121", 950: "#121212",
				},
				danger: { DEFAULT: "#E21B22", soft: "#FDE3E4", dark: "#B9151B" },
				success: { DEFAULT: "#2E9E5B", soft: "#E3F3E8" },
				warning: { DEFAULT: "#F2A23A", soft: "#FCEBD9", deep: "#E08A1E" },
				avatar: "#FFBF48",
				lavender: { DEFAULT: "#E9E8FB", deep: "#5B5BD6" },
				lime: "#B7E34B",
			},
			fontFamily: {
				sans: ["-apple-system", "system-ui", '"Segoe UI"', "Helvetica", "Arial", "sans-serif"],
			},
			boxShadow: {
				card: "0 1px 3px rgba(0,0,0,.06)",
				lift: "0 8px 24px rgba(0,0,0,.12)",
				fab: "0 6px 16px rgba(4,142,255,.35)",
			},
			borderRadius: { xl: "12px", "2xl": "16px" },
			maxWidth: { app: "480px" },
			keyframes: {
				halo: { "0%,100%": { transform: "scale(1)", opacity: ".9" }, "50%": { transform: "scale(1.08)", opacity: ".55" } },
				shimmer: { "100%": { transform: "translateX(100%)" } },
			},
			animation: { halo: "halo 2.2s ease-in-out infinite", shimmer: "shimmer 1.4s infinite" },
		},
	},
	plugins: [],
}
