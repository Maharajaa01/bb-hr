<script setup lang="ts">
import { useOnline } from "@vueuse/core"
import { useIntervalFn } from "@vueuse/core"
import {
	AlertTriangle,
	Camera,
	CheckCircle2,
	Circle,
	Crosshair,
	Hand,
	MapPin,
	MapPinOff,
	RefreshCw,
	RotateCcw,
	Timer,
	WifiOff,
} from "lucide-vue-next"
import { computed, nextTick, onMounted, ref } from "vue"

import { ApiError, call } from "@/api/client"
import type { AttendanceStatus, PunchResult } from "@/api/types"
import AppBar from "@/components/ui/AppBar.vue"
import HeaderTabs from "@/components/ui/HeaderTabs.vue"
import AppButton from "@/components/ui/AppButton.vue"
import Avatar from "@/components/ui/Avatar.vue"
import ErrorState from "@/components/ui/ErrorState.vue"
import LogTable from "@/components/ui/LogTable.vue"
import Skeleton from "@/components/ui/Skeleton.vue"
import Spinner from "@/components/ui/Spinner.vue"
import { useCamera } from "@/composables/useCamera"
import { useGeolocation } from "@/composables/useGeolocation"
import { useResource } from "@/composables/useResource"
import { clock, formatDate, formatDistance, formatTime, parseLocal, titleCase } from "@/lib/format"
import { nearestLocation, withinGeofence } from "@/lib/geo"
import { deviceLabel, newRequestId } from "@/lib/id"
import { useSession } from "@/stores/session"

const online = useOnline()
const session = useSession()
const { data: status, error: loadError, loading, reload } = useResource((signal) =>
	call<AttendanceStatus>("attendance.get_status", {}, { signal }),
)

const geo = useGeolocation({ maxWaitMs: 15000, goodEnough: 25 })
const video = ref<HTMLVideoElement | null>(null)
const camera = useCamera(video)
const photo = ref<string | null>(null)

const submitting = ref(false)
const result = ref<PunchResult | null>(null)
/** Server refused the punch - nothing was recorded. */
const rejection = ref<ApiError | null>(null)
/** We don't know whether the punch was recorded (network died mid-request). */
const uncertain = ref(false)
let requestId: string | null = null

const action = computed(() => status.value?.next_action ?? "IN")
const actionLabel = computed(() => (action.value === "IN" ? "Check in" : "Check out"))
const rules = computed(() => status.value?.rules)

const nearest = computed(() => {
	const fix = geo.fix.value
	if (!fix || !rules.value?.locations.length) return null
	return nearestLocation(fix.latitude, fix.longitude, rules.value.locations)
})

/** Client-side preview of the server's geofence decision. The server re-checks everything. */
const locationState = computed<"pending" | "ok" | "outside" | "weak" | "unconfigured" | "error" | "unrestricted">(() => {
	const r = rules.value
	if (!r) return "pending"
	if (!r.geofence) return "unrestricted"
	if (!r.locations.length) return "unconfigured"
	if (geo.error.value) return "error"
	const fix = geo.fix.value
	if (!fix) return "pending"
	if (fix.accuracy > r.max_accuracy) return "weak"
	if (!nearest.value) return "pending"
	return withinGeofence(nearest.value.distance, nearest.value.radius, fix.accuracy, r.accuracy_tolerance) ? "ok" : "outside"
})

const photoRequired = computed(() => !!rules.value?.require_photo)
const ready = computed(
	() =>
		online.value &&
		!submitting.value &&
		(locationState.value === "ok" || locationState.value === "unrestricted") &&
		(!photoRequired.value || !!photo.value),
)

const blocker = computed(() => {
	if (!online.value) return "You're offline. Connect to the internet to " + actionLabel.value.toLowerCase() + "."
	switch (locationState.value) {
		case "pending":
			return geo.locating.value ? "Finding your location…" : "Get your location to continue."
		case "unconfigured":
			return "No office location is set up yet. Ask HR to add one in BB HR Settings."
		case "error":
			return geo.error.value?.message ?? "Location unavailable."
		case "weak":
			return `Your GPS fix is too rough (±${Math.round(geo.fix.value!.accuracy)} m). Move near a window or outdoors and refresh.`
		case "outside":
			return `You're ${formatDistance(nearest.value!.distance)} from ${nearest.value!.location.name}. Move within ${nearest.value!.radius} m to continue.`
	}
	if (photoRequired.value && !photo.value) return "Take a selfie to continue."
	return ""
})

onMounted(() => {
	void geo.locate()
})

async function startCamera() {
	photo.value = null
	const ok = await camera.start()
	if (ok) await nextTick()
}

function capture() {
	const shot = camera.capture()
	if (shot) {
		photo.value = shot
		camera.stop()
	}
}

function retake() {
	photo.value = null
	void startCamera()
}

async function submit() {
	if (!ready.value) return
	submitting.value = true
	rejection.value = null
	uncertain.value = false
	requestId = requestId ?? newRequestId()
	const fix = geo.fix.value
	try {
		const res = await call<PunchResult>(
			"attendance.punch",
			{
				log_type: action.value,
				latitude: fix?.latitude,
				longitude: fix?.longitude,
				accuracy: fix?.accuracy,
				photo: photo.value,
				request_id: requestId,
				device: deviceLabel(),
			},
			{ method: "POST" },
		)
		// success only when the server hands back the record it created
		if (res?.ok && res.checkin) {
			result.value = res
			requestId = null
			photo.value = null
			void reload()
		} else {
			uncertain.value = true
		}
	} catch (e) {
		const err = e instanceof ApiError ? e : new ApiError(String(e))
		if (err.isNetwork || err.status >= 500) {
			// keep requestId: a retry returns the original punch if it did go through
			uncertain.value = true
		} else {
			rejection.value = err
			requestId = null
		}
	} finally {
		submitting.value = false
	}
}

function startOver() {
	result.value = null
	rejection.value = null
	uncertain.value = false
	photo.value = null
	void geo.locate()
}

// ---- presentation helpers -------------------------------------------------
/** Server clock offset, so the timer follows server time rather than the phone's clock. */
const skewMs = computed(() => {
	const server = parseLocal(status.value?.server_time)
	return server ? server.getTime() - Date.now() : 0
})
const nowMs = ref(Date.now())
useIntervalFn(() => (nowMs.value = Date.now()), 1000)

/** Worked time today, ticking while checked in. */
const workedSeconds = computed(() => {
	const logs = status.value?.logs ?? []
	let total = 0
	let open: number | null = null
	for (const l of logs) {
		const t = parseLocal(l.time)?.getTime() ?? 0
		if (l.log_type === "IN") open = open ?? t
		else if (open !== null) {
			total += (t - open) / 1000
			open = null
		}
	}
	if (open !== null) total += (nowMs.value + skewMs.value - open) / 1000
	return total
})

const pairs = computed(() => {
	const out: { key: string; in: string; out: string; duration: string }[] = []
	let current: { in: string; inTime: number } | null = null
	for (const l of status.value?.logs ?? []) {
		const t = parseLocal(l.time)?.getTime() ?? 0
		if (l.log_type === "IN") current = { in: l.time, inTime: t }
		else if (current) {
			out.push({ key: l.name, in: formatTime(current.in), out: formatTime(l.time), duration: clock((t - current.inTime) / 1000).replace(/ /g, "") })
			current = null
		}
	}
	if (current) out.push({ key: "open", in: formatTime(current.in), out: "--:--", duration: clock((nowMs.value + skewMs.value - current.inTime) / 1000).replace(/ /g, "") })
	return out
})

const lastIn = computed(() => [...(status.value?.logs ?? [])].reverse().find((l) => l.log_type === "IN"))
const isOut = computed(() => action.value === "OUT")
</script>

<template>
	<div>
		<AppBar :title="result ? 'Done' : 'Check In / Out'" back="/">
			<template #extension>
				<HeaderTabs :tabs="[{ to: '/check-in', label: 'Today' }, { to: '/attendance', label: 'Overview' }]" />
				<div class="flex items-center gap-3 border-t border-white/20 px-4 pb-3 pt-3">
					<Avatar :name="session.displayName" :image="session.employee?.image" size="md" />
					<div class="min-w-0">
						<p class="truncate text-base font-medium">{{ titleCase(session.displayName) }}</p>
						<p class="text-[13px] text-white/90">{{ session.employee?.name }}</p>
					</div>
				</div>
			</template>
		</AppBar>

		<ErrorState v-if="loadError && !status" :error="loadError" :retrying="loading" @retry="reload" />
		<div v-else-if="!status" class="space-y-3 pt-4"><Skeleton :lines="2" /><div class="mx-auto h-[140px] w-[140px] animate-pulse rounded-full bg-ink-100" /><Skeleton card :lines="4" /></div>

		<!-- confirmed by the server -->
		<section v-else-if="result" v-motion :initial="{ opacity: 0, scale: 0.96 }" :enter="{ opacity: 1, scale: 1 }" class="px-3 py-10 text-center" role="status">
			<div class="mx-auto mb-4 grid h-20 w-20 place-items-center rounded-full bg-success-soft text-success"><CheckCircle2 class="h-11 w-11" /></div>
			<p class="text-xl font-semibold">{{ result.message }}</p>
			<p class="mt-1 text-ink-500">
				<template v-if="result.location">at {{ result.location }}<template v-if="result.distance !== null"> · {{ formatDistance(result.distance) }} away</template></template>
				<template v-else>Recorded</template>
			</p>
			<p class="mt-1 text-xs text-ink-400">Reference {{ result.checkin }}</p>
			<p v-if="result.warning" class="mt-4 rounded-xl bg-warning-soft px-3 py-2 text-left text-sm text-warning-deep">{{ result.warning }}</p>
			<div class="mt-6 grid grid-cols-2 gap-2.5">
				<AppButton to="/" variant="secondary">Home</AppButton>
				<AppButton @click="startOver">Done</AppButton>
			</div>
		</section>

		<div v-else>
			<!-- date, timer, punch button -->
			<section class="flex flex-col items-center pt-2 text-center">
				<p class="text-[13px] text-ink-500">{{ formatDate(status.date, { year: true }) }}</p>
				<p class="tabular mt-1 flex items-center gap-2 text-[25px] font-semibold"><Timer class="h-6 w-6 text-danger" />{{ clock(workedSeconds) }}</p>
				<p v-if="status.holiday" class="mt-1 rounded-full bg-brand-50 px-3 py-0.5 text-[13px] text-brand-600">{{ status.holiday.weekly_off ? "Weekly off" : status.holiday.description }} · you can still punch</p>

				<div class="relative my-6 grid h-[140px] w-[140px] place-items-center">
					<span class="absolute inset-0 rounded-full" :class="[isOut ? 'bg-danger-soft' : 'bg-brand-100', ready && !submitting ? 'animate-halo' : '']" aria-hidden="true" />
					<button
						class="relative grid h-[100px] w-[100px] place-items-center rounded-full text-white shadow-lift transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-60"
						:class="isOut ? 'bg-danger' : 'bg-brand-500'"
						:disabled="!ready"
						:aria-label="submitting ? 'Confirming with server' : uncertain ? `Retry ${actionLabel.toLowerCase()}` : `Confirm ${actionLabel.toLowerCase()}`"
						@click="submit"
					>
						<Spinner v-if="submitting" class="h-9 w-9" />
						<Hand v-else class="h-11 w-11" :stroke-width="1.6" />
					</button>
				</div>

				<p class="text-[14px]">
					<template v-if="lastIn">Your last check in was {{ formatTime(lastIn.time) }}</template>
					<template v-else>You have not checked in today</template>
				</p>
				<p class="mt-0.5 text-[13px] text-ink-500">
					{{ submitting ? "Confirming with server…" : ready ? `Click here to ${isOut ? "Check Out" : "Check In"}` : blocker }}
				</p>
			</section>

			<!-- requirements: location + selfie -->
			<section class="mt-5 space-y-2.5">
				<div class="card flex items-center gap-3 p-3">
					<span
						class="grid h-10 w-10 shrink-0 place-items-center rounded-full"
						:class="['ok', 'unrestricted'].includes(locationState) ? 'bg-success-soft text-success' : ['outside', 'error'].includes(locationState) ? 'bg-danger-soft text-danger' : ['weak', 'unconfigured'].includes(locationState) ? 'bg-warning-soft text-warning-deep' : 'bg-ink-100 text-ink-500'"
					>
						<Spinner v-if="geo.locating.value && !geo.fix.value" class="h-5 w-5" />
						<MapPinOff v-else-if="['outside', 'error'].includes(locationState)" class="h-5 w-5" />
						<Crosshair v-else-if="locationState === 'ok'" class="h-5 w-5" />
						<MapPin v-else class="h-5 w-5" />
					</span>
					<div class="min-w-0 flex-1 text-[14px]">
						<p v-if="locationState === 'ok'" class="truncate font-medium text-success">Inside {{ nearest!.location.name }}</p>
						<p v-else-if="locationState === 'unrestricted'" class="truncate font-medium">Location check is off</p>
						<p v-else-if="locationState === 'outside'" class="truncate font-medium text-danger">Outside the office area</p>
						<p v-else-if="locationState === 'error'" class="truncate font-medium text-danger">Location unavailable</p>
						<p v-else-if="locationState === 'weak'" class="truncate font-medium text-warning-deep">Weak GPS signal</p>
						<p v-else-if="locationState === 'unconfigured'" class="truncate font-medium text-warning-deep">Office location not set up</p>
						<p v-else class="truncate font-medium">{{ geo.locating.value ? "Finding your location…" : "Location needed" }}</p>
						<p class="truncate text-[13px] text-ink-500">
							<template v-if="locationState === 'ok'">{{ formatDistance(nearest!.distance) }} away · GPS ±{{ Math.round(geo.fix.value!.accuracy) }} m</template>
							<template v-else-if="locationState === 'error'">{{ geo.error.value?.message }}</template>
							<template v-else-if="locationState === 'pending'">Allow location when your phone asks</template>
							<template v-else-if="locationState === 'unrestricted'">Your position is recorded with the punch</template>
							<template v-else>{{ blocker }}</template>
						</p>
					</div>
					<button class="grid h-11 w-11 shrink-0 place-items-center rounded-full text-brand-500 hover:bg-brand-50 disabled:opacity-50" :disabled="geo.locating.value" aria-label="Refresh location" @click="geo.locate()">
						<RefreshCw class="h-5 w-5" :class="geo.locating.value ? 'animate-spin' : ''" />
					</button>
				</div>

				<div v-if="photoRequired" class="card p-3">
					<div v-show="camera.active.value" class="relative mb-3 overflow-hidden rounded-xl bg-ink-950">
						<video ref="video" class="aspect-square w-full -scale-x-100 object-cover" playsinline muted autoplay />
						<div class="absolute inset-x-0 bottom-0 flex justify-center p-4">
							<button class="grid h-16 w-16 place-items-center rounded-full border-4 border-white bg-white/20 backdrop-blur active:scale-95" aria-label="Take photo" @click="capture"><span class="h-11 w-11 rounded-full bg-white" /></button>
						</div>
					</div>
					<div class="flex items-center gap-3">
						<img v-if="photo" :src="photo" alt="Your selfie" class="h-10 w-10 shrink-0 rounded-full object-cover" />
						<span v-else class="grid h-10 w-10 shrink-0 place-items-center rounded-full" :class="camera.error.value ? 'bg-danger-soft text-danger' : 'bg-ink-100 text-ink-500'"><Camera class="h-5 w-5" /></span>
						<div class="min-w-0 flex-1 text-[14px]">
							<p class="truncate font-medium" :class="photo ? 'text-success' : ''">{{ photo ? "Photo ready" : "Selfie required" }}</p>
							<p class="truncate text-[13px]" :class="camera.error.value ? 'text-danger' : 'text-ink-500'">{{ camera.error.value?.message ?? (photo ? "Tap retake to change it" : "Take a quick photo to confirm it's you") }}</p>
						</div>
						<button v-if="photo" class="inline-flex h-11 shrink-0 items-center gap-1 rounded-full px-3 text-[14px] font-medium text-brand-500 hover:bg-brand-50" @click="retake"><RotateCcw class="h-4 w-4" />Retake</button>
						<button v-else-if="!camera.active.value" class="inline-flex h-11 shrink-0 items-center gap-1 rounded-full px-3 text-[14px] font-medium text-brand-500 hover:bg-brand-50" :disabled="camera.starting.value" @click="startCamera">
							<Spinner v-if="camera.starting.value" class="h-4 w-4" />{{ camera.error.value ? "Retry" : "Camera" }}
						</button>
					</div>
				</div>

				<div v-if="rejection" class="flex gap-3 rounded-xl border border-danger/30 bg-danger-soft p-3.5 text-[14px] text-danger-dark" role="alert">
					<AlertTriangle class="mt-0.5 h-5 w-5 shrink-0" />
					<div><p class="font-semibold">{{ rejection.title || "Not recorded" }}</p><p>{{ rejection.message }}</p></div>
				</div>
				<div v-if="uncertain" class="flex gap-3 rounded-xl border border-warning/40 bg-warning-soft p-3.5 text-[14px] text-warning-deep" role="alert">
					<WifiOff class="mt-0.5 h-5 w-5 shrink-0" />
					<div>
						<p class="font-semibold">We couldn't confirm your {{ actionLabel.toLowerCase() }}</p>
						<p>The connection dropped, so it may not have been recorded. Tap the button again when you're back online — it will not be recorded twice.</p>
					</div>
				</div>
			</section>

			<!-- summary -->
			<section class="-mx-3 mt-5 grid grid-cols-3 border-t border-ink-200 text-center">
				<div class="py-3"><p class="tabular font-semibold">{{ status.first_in ? formatTime(status.first_in) : "--:--" }}</p><p class="mt-0.5 inline-flex items-center gap-1 text-[13px] text-ink-500"><Circle class="h-2.5 w-2.5 fill-brand-500 text-brand-500" />From</p></div>
				<div class="border-x border-ink-200 py-3"><p class="tabular font-semibold">{{ status.last_out ? formatTime(status.last_out) : "--:--" }}</p><p class="mt-0.5 inline-flex items-center gap-1 text-[13px] text-ink-500"><Circle class="h-2.5 w-2.5 fill-danger text-danger" />To</p></div>
				<div class="py-3"><p class="tabular font-semibold text-brand-500">{{ clock(workedSeconds).replace(/ /g, "") }}</p><p class="mt-0.5 text-[13px] text-ink-500">Working Hrs</p></div>
			</section>

			<!-- log -->
			<section class="-mx-3"><LogTable :rows="pairs" empty="No punches yet today" /></section>
		</div>
	</div>
</template>
