import {
	AlertTriangle,
	BarChart3,
	CalendarDays,
	CalendarRange,
	Fingerprint,
	Home,
	IndianRupee,
	type LucideIcon,
	UserCircle,
	Users,
	UsersRound,
} from "lucide-vue-next"

import type { SpotName } from "@/components/illustrations/Spot.vue"

export interface NavItem {
	to: string
	label: string
	icon: LucideIcon
	spot: SpotName
	access?: "employee" | "team" | "hr"
}

/** Every destination, in drawer / quick-link order. Visibility is filtered by role in the shell. */
export const NAV: NavItem[] = [
	{ to: "/", label: "Dashboard", icon: Home, spot: "profile", access: "employee" },
	{ to: "/check-in", label: "Check In/Out", icon: Fingerprint, spot: "checkin", access: "employee" },
	{ to: "/attendance", label: "Attendance", icon: CalendarRange, spot: "attendance", access: "employee" },
	{ to: "/salary", label: "Salary Slip", icon: IndianRupee, spot: "salary", access: "employee" },
	{ to: "/holidays", label: "Holiday List", icon: CalendarDays, spot: "holiday", access: "employee" },
	{ to: "/directory", label: "Directory", icon: UsersRound, spot: "directory", access: "team" },
	{ to: "/team", label: "Team Attendance", icon: Users, spot: "team", access: "team" },
	{ to: "/exceptions", label: "Exceptions", icon: AlertTriangle, spot: "alert", access: "team" },
	{ to: "/hr", label: "HR Dashboard", icon: BarChart3, spot: "chart", access: "hr" },
	{ to: "/profile", label: "My Profile", icon: UserCircle, spot: "profile" },
]
