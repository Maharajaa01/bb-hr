/** Mirrors bb_academy_hrms/utils/geo.py so the client can preview what the server will decide. */

import type { OfficeLocation } from "@/api/types"

const EARTH_RADIUS_M = 6371000

export function haversine(lat1: number, lon1: number, lat2: number, lon2: number): number {
	const rad = (d: number) => (d * Math.PI) / 180
	const dPhi = rad(lat2 - lat1)
	const dLambda = rad(lon2 - lon1)
	const a = Math.sin(dPhi / 2) ** 2 + Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(dLambda / 2) ** 2
	return Math.round(2 * EARTH_RADIUS_M * Math.asin(Math.sqrt(a)) * 100) / 100
}

export function isValidCoordinate(lat: unknown, lon: unknown): boolean {
	const la = Number(lat)
	const lo = Number(lon)
	if (!Number.isFinite(la) || !Number.isFinite(lo)) return false
	if (la === 0 && lo === 0) return false
	return la >= -90 && la <= 90 && lo >= -180 && lo <= 180
}

export interface Nearest {
	location: OfficeLocation
	distance: number
	radius: number
}

export function nearestLocation(lat: number, lon: number, locations: OfficeLocation[]): Nearest | null {
	let best: Nearest | null = null
	for (const loc of locations) {
		const distance = haversine(lat, lon, loc.latitude, loc.longitude)
		if (!best || distance < best.distance) best = { location: loc, distance, radius: loc.radius }
	}
	return best
}

export function withinGeofence(distance: number, radius: number, accuracy = 0, tolerance = 0): boolean {
	const slack = Math.min(Math.max(accuracy, 0), tolerance)
	return distance <= radius + slack
}
