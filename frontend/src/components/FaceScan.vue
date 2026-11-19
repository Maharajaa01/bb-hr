<script setup lang="ts">
/**
 * Face-lock style scan: a few frames looking straight, then a few while turning the head
 * the way the server asked. Only captures; the server enrols or matches the face.
 */
import { ArrowLeft, ArrowRight, RotateCcw, ScanFace, ShieldCheck } from "lucide-vue-next"
import { computed, nextTick, onBeforeUnmount, ref } from "vue"

import { ApiError, call } from "@/api/client"
import type { FaceChallenge, FaceScanResult } from "@/api/types"
import Spinner from "@/components/ui/Spinner.vue"
import { useCamera } from "@/composables/useCamera"

const props = defineProps<{ enrolled: boolean }>()
const scan = defineModel<FaceScanResult | null>({ required: true })

const video = ref<HTMLVideoElement | null>(null)
const camera = useCamera(video)

type Phase = "idle" | "preparing" | "front" | "turn" | "done"
const phase = ref<Phase>("idle")
const direction = ref<"left" | "right">("left")
const countdown = ref(0)
const error = ref<string | null>(null)
let expiryTimer: ReturnType<typeof setTimeout> | undefined
let cancelled = false

const FRONT_FRAMES = 3
const TURN_AT_MS = [900, 1400, 1900, 2400]
const SNAP = { maxSize: 480, quality: 0.85 }

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))
const busy = computed(() => ["preparing", "front", "turn"].includes(phase.value))

const instruction = computed(() => {
	switch (phase.value) {
		case "preparing":
			return "Starting camera…"
		case "front":
			return countdown.value > 0 ? `Look straight at the camera · ${countdown.value}` : "Hold still…"
		case "turn":
			return `Slowly turn your head to the ${direction.value}`
	}
	return ""
})

function snap(): string {
	const shot = camera.capture(SNAP.maxSize, SNAP.quality)
	if (!shot) throw new Error("The camera stopped. Please try again.")
	return shot
}

async function waitForVideo() {
	for (let i = 0; i < 40 && !(video.value?.videoWidth ?? 0); i++) await sleep(100)
	if (!video.value?.videoWidth) throw new Error("The camera did not start. Please try again.")
	await sleep(500) // let exposure settle
}

async function start() {
	cancelled = false
	error.value = null
	scan.value = null
	phase.value = "preparing"
	try {
		const challenge = await call<FaceChallenge>("face.challenge", {}, { method: "POST" })
		if (!challenge.enabled || !challenge.token) throw new Error("Face verification is turned off. Reload the page.")
		direction.value = challenge.direction
		if (!(await camera.start())) {
			phase.value = "idle"
			return
		}
		await nextTick()
		await waitForVideo()

		phase.value = "front"
		for (countdown.value = 3; countdown.value > 0; countdown.value--) {
			await sleep(500)
			if (cancelled) return
		}
		const front: string[] = []
		for (let i = 0; i < FRONT_FRAMES; i++) {
			front.push(snap())
			await sleep(250)
		}

		const turn: string[] = []
		if (challenge.liveness) {
			phase.value = "turn"
			let elapsed = 0
			for (const at of TURN_AT_MS) {
				await sleep(at - elapsed)
				elapsed = at
				if (cancelled) return
				turn.push(snap())
			}
		}

		camera.stop()
		scan.value = { token: challenge.token, front, turn, preview: front[0] }
		phase.value = "done"
		// the server forgets the challenge after `expires_in`; ask for a fresh scan a little before
		clearTimeout(expiryTimer)
		expiryTimer = setTimeout(() => reset("Your scan expired. Scan again."), Math.max(10, challenge.expires_in - 15) * 1000)
	} catch (e) {
		camera.stop()
		phase.value = "idle"
		error.value = e instanceof ApiError ? e.message : (e as Error).message
	}
}

function reset(message: string | null = null) {
	cancelled = true
	clearTimeout(expiryTimer)
	camera.stop()
	scan.value = null
	phase.value = "idle"
	error.value = message
}

onBeforeUnmount(() => {
	cancelled = true
	clearTimeout(expiryTimer)
})

defineExpose({ reset })
</script>

<template>
	<div class="card p-3">
		<div v-show="busy" class="mb-3 flex flex-col items-center">
			<div class="relative h-56 w-56">
				<video ref="video" class="h-full w-full -scale-x-100 rounded-full bg-ink-950 object-cover" playsinline muted autoplay />
				<span
					class="pointer-events-none absolute -inset-1.5 rounded-full border-4 transition-colors"
					:class="phase === 'turn' ? 'animate-pulse border-brand-500' : phase === 'front' && countdown === 0 ? 'border-success' : 'border-white/70'"
					aria-hidden="true"
				/>
				<span v-if="phase === 'turn'" class="absolute top-1/2 grid h-11 w-11 -translate-y-1/2 place-items-center rounded-full bg-brand-500 text-white shadow-lift" :class="direction === 'left' ? '-left-5' : '-right-5'" aria-hidden="true">
					<ArrowLeft v-if="direction === 'left'" class="h-6 w-6" /><ArrowRight v-else class="h-6 w-6" />
				</span>
			</div>
			<p class="mt-3 text-center text-[15px] font-medium" role="status" aria-live="assertive">{{ instruction }}</p>
		</div>

		<div class="flex items-center gap-3">
			<img v-if="scan" :src="scan.preview" alt="Your face scan" class="h-10 w-10 shrink-0 rounded-full object-cover" />
			<span v-else class="grid h-10 w-10 shrink-0 place-items-center rounded-full" :class="error || camera.error.value ? 'bg-danger-soft text-danger' : 'bg-brand-50 text-brand-500'">
				<ScanFace class="h-5 w-5" />
			</span>
			<div class="min-w-0 flex-1 text-[14px]">
				<p class="truncate font-medium" :class="scan ? 'text-success' : ''">
					{{ scan ? "Face scanned" : props.enrolled ? "Face check required" : "Set up face check-in" }}
				</p>
				<p class="text-[13px]" :class="error || camera.error.value ? 'text-danger' : 'text-ink-500'">
					{{
						error ??
						camera.error.value?.message ??
						(scan
							? "Ready — you can confirm now"
							: props.enrolled
								? "Scan your face to confirm it's you"
								: "First time only: we'll save your face to recognise you next time")
					}}
				</p>
			</div>
			<button v-if="scan" class="inline-flex h-11 shrink-0 items-center gap-1 rounded-full px-3 text-[14px] font-medium text-brand-500 hover:bg-brand-50" @click="start"><RotateCcw class="h-4 w-4" />Rescan</button>
			<button v-else-if="!busy" class="inline-flex h-11 shrink-0 items-center gap-1 rounded-full px-3 text-[14px] font-medium text-brand-500 hover:bg-brand-50" @click="start">
				<ScanFace class="h-4 w-4" />{{ error || camera.error.value ? "Retry" : "Scan" }}
			</button>
			<Spinner v-else-if="phase === 'preparing'" class="h-5 w-5 shrink-0 text-brand-500" />
		</div>
		<p v-if="!props.enrolled && !scan && !busy" class="mt-2 flex items-start gap-1.5 text-[12px] text-ink-500">
			<ShieldCheck class="mt-px h-3.5 w-3.5 shrink-0" />Your face data is stored privately and only used to verify your punches. HR can reset it.
		</p>
	</div>
</template>
