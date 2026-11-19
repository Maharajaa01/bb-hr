<script setup lang="ts">
import { ArrowLeft, Eye, EyeOff, Mail } from "lucide-vue-next"
import { nextTick, ref } from "vue"
import { useRoute } from "vue-router"

import { ApiError } from "@/api/client"
import BrandLogo from "@/components/BrandLogo.vue"
import Spot from "@/components/illustrations/Spot.vue"
import AppButton from "@/components/ui/AppButton.vue"
import { useSession } from "@/stores/session"

const session = useSession()
const route = useRoute()
const step = ref<"email" | "password">("email")
const email = ref("")
const password = ref("")
const show = ref(false)
const busy = ref(false)
const error = ref("")
const passwordInput = ref<HTMLInputElement | null>(null)

async function next() {
	error.value = ""
	if (!email.value.trim()) {
		error.value = "Enter your email or username."
		return
	}
	step.value = "password"
	await nextTick()
	passwordInput.value?.focus()
}

async function submit() {
	if (!password.value) {
		error.value = "Enter your password."
		return
	}
	busy.value = true
	error.value = ""
	try {
		await session.login(email.value.trim(), password.value)
		// full navigation: the page must be re-rendered to carry the new session's CSRF token
		const target = typeof route.query.redirect === "string" && route.query.redirect.startsWith("/") ? route.query.redirect : "/"
		window.location.replace(`/bbhr${target}`)
	} catch (e) {
		error.value = e instanceof ApiError ? e.message : "Sign-in failed. Please try again."
		busy.value = false
	}
}

function back() {
	step.value = "email"
	password.value = ""
	error.value = ""
}
</script>

<template>
	<div class="min-h-screen bg-white lg:grid lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
	<!-- desktop: brand panel on the left -->
	<aside class="relative hidden overflow-hidden bg-gradient-to-br from-brand-500 to-brand-800 p-12 text-white lg:flex lg:flex-col">
		<span class="absolute -right-24 -top-24 h-80 w-80 rounded-full bg-white/10" aria-hidden="true" />
		<span class="absolute -bottom-32 -left-20 h-96 w-96 rounded-full bg-white/5" aria-hidden="true" />
		<div class="relative flex items-center gap-3">
			<span class="grid h-12 w-12 place-items-center rounded-2xl bg-white text-[17px] font-black text-brand-600">BB</span>
			<span><span class="block text-[22px] font-bold leading-none">BB HRMS</span><span class="text-[13px] text-white/80">Black Building Academy</span></span>
		</div>
		<div class="relative my-auto">
			<div class="mx-auto mb-10 max-w-md rounded-3xl bg-white/95 p-6 shadow-lift"><Spot name="login" class="h-56 w-full" /></div>
			<h2 class="text-3xl font-semibold leading-tight">Attendance, shifts and payslips<br />in one place.</h2>
			<p class="mt-3 max-w-md text-white/85">Check in with your fingerprint or phone, see your attendance and download payslips — HR manages shifts and the team from the same app.</p>
		</div>
	</aside>

	<div class="mx-auto flex min-h-screen max-w-app flex-col bg-white px-5 pb-8 safe-top safe-bottom sm:shadow-lift lg:w-full lg:max-w-md lg:justify-center lg:px-8 lg:shadow-none">
		<div v-motion :initial="{ opacity: 0, y: 10 }" :enter="{ opacity: 1, y: 0 }" class="pt-12 lg:pt-0">
			<BrandLogo />
		</div>

		<div class="mt-8 flex justify-center lg:hidden"><Spot name="login" class="h-44 w-full max-w-[300px]" /></div>

		<form class="mt-8 flex flex-1 flex-col lg:mt-10 lg:flex-none" novalidate @submit.prevent="step === 'email' ? next() : submit()">
			<h1 class="text-[22px] font-semibold text-ink-900">Login to Your Account</h1>
			<p class="mt-1 text-[14px] text-ink-500">{{ step === "email" ? "Use the login HR gave you." : "Enter your password to continue." }}</p>

			<div v-if="step === 'email'" class="mt-6">
				<label class="label" for="email">Email or username</label>
				<div class="relative">
					<Mail class="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-400" />
					<input id="email" v-model="email" class="field pl-11" type="text" autocomplete="username" inputmode="email" autocapitalize="off" spellcheck="false" autofocus required />
				</div>
			</div>

			<div v-else class="mt-6 space-y-4">
				<button type="button" class="flex w-full items-center gap-2 rounded-[10px] bg-ink-100 px-3 py-2.5 text-left text-[14px]" @click="back">
					<ArrowLeft class="h-4 w-4 text-ink-500" /><span class="min-w-0 flex-1 truncate">{{ email }}</span><span class="text-brand-500">Change</span>
				</button>
				<div>
					<label class="label" for="password">Password</label>
					<div class="relative">
						<input id="password" ref="passwordInput" v-model="password" class="field pr-12" :type="show ? 'text' : 'password'" autocomplete="current-password" required />
						<button type="button" class="absolute inset-y-0 right-0 grid w-12 place-items-center text-ink-400 hover:text-ink-700" :aria-label="show ? 'Hide password' : 'Show password'" @click="show = !show">
							<EyeOff v-if="show" class="h-5 w-5" /><Eye v-else class="h-5 w-5" />
						</button>
					</div>
				</div>
				<!-- keep the username in the form so password managers pair them -->
				<input type="text" :value="email" autocomplete="username" class="hidden" tabindex="-1" aria-hidden="true" readonly />
			</div>

			<p v-if="error" class="mt-4 rounded-[10px] bg-danger-soft px-3 py-2.5 text-[14px] text-danger-dark" role="alert">{{ error }}</p>

			<div class="mt-auto pt-8 lg:mt-0">
				<AppButton type="submit" block :loading="busy">{{ step === "email" ? "Next" : "Login" }}</AppButton>
				<p class="mt-4 text-center text-[14px]"><a href="/login#forgot" class="text-brand-500">Forgot password?</a></p>
			</div>
		</form>
	</div>
	</div>
</template>
