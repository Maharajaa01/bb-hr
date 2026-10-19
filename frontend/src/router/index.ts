import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router"

import { useSession } from "@/stores/session"

declare module "vue-router" {
	interface RouteMeta {
		title?: string
		public?: boolean
		/** employee: needs a linked, active Employee. team: reporting manager or HR. hr: HR only. */
		access?: "employee" | "team" | "hr"
	}
}

const routes: RouteRecordRaw[] = [
	{ path: "/login", name: "login", component: () => import("@/views/Login.vue"), meta: { public: true, title: "Sign in" } },
	{
		path: "/",
		component: () => import("@/layouts/AppShell.vue"),
		children: [
			{ path: "", name: "home", component: () => import("@/views/Dashboard.vue"), meta: { access: "employee", title: "Home" } },
			{ path: "check-in", name: "check-in", component: () => import("@/views/CheckIn.vue"), meta: { access: "employee", title: "Check in" } },
			{ path: "attendance", name: "attendance", component: () => import("@/views/AttendanceHistory.vue"), meta: { access: "employee", title: "My attendance" } },
			{ path: "salary", name: "salary", component: () => import("@/views/SalarySlips.vue"), meta: { access: "employee", title: "Salary slips" } },
			{ path: "salary/:name(.*)", name: "salary-slip", component: () => import("@/views/SalarySlipDetail.vue"), props: true, meta: { title: "Payslip" } },
			{ path: "holidays", name: "holidays", component: () => import("@/views/Holidays.vue"), meta: { access: "employee", title: "Holidays" } },
			{ path: "team", name: "team", component: () => import("@/views/Team.vue"), meta: { access: "team", title: "Team attendance" } },
			{ path: "team/:employee", name: "team-member", component: () => import("@/views/AttendanceHistory.vue"), props: true, meta: { access: "team", title: "Attendance" } },
			{ path: "exceptions", name: "exceptions", component: () => import("@/views/Exceptions.vue"), meta: { access: "team", title: "Exceptions" } },
			{ path: "directory", name: "directory", component: () => import("@/views/Directory.vue"), meta: { access: "team", title: "Directory" } },
			{ path: "hr", name: "hr", component: () => import("@/views/HrDashboard.vue"), meta: { access: "hr", title: "HR dashboard" } },
			{ path: "hr/salary/:employee", name: "hr-salary", component: () => import("@/views/SalarySlips.vue"), props: true, meta: { access: "hr", title: "Salary slips" } },
			{ path: "profile", name: "profile", component: () => import("@/views/Profile.vue"), meta: { title: "Profile" } },
			{ path: "no-employee", name: "no-employee", component: () => import("@/views/NoEmployee.vue"), meta: { title: "Account not linked" } },
			{ path: "forbidden", name: "forbidden", component: () => import("@/views/Forbidden.vue"), meta: { title: "Not allowed" } },
			{ path: ":pathMatch(.*)*", name: "not-found", component: () => import("@/views/NotFound.vue"), meta: { title: "Not found" } },
		],
	},
]

export const router = createRouter({
	history: createWebHistory("/bbhr/"),
	routes,
	scrollBehavior: (_to, _from, saved) => saved ?? { top: 0 },
})

router.beforeEach(async (to) => {
	const session = useSession()
	try {
		await session.load()
	} catch {
		// offline on first load: let the shell render its offline state
		if (!to.meta.public) return true
	}

	if (to.meta.public) {
		return session.isLoggedIn && to.name === "login" ? { name: "home" } : true
	}
	if (!session.isLoggedIn) {
		return { name: "login", query: to.fullPath !== "/" ? { redirect: to.fullPath } : {} }
	}

	const access = to.meta.access
	if (access === "employee" && !session.isEmployee) {
		// HR/admin users without an employee record land on the HR dashboard instead
		if (to.name === "home" && session.isHr) return { name: "hr" }
		return { name: "no-employee" }
	}
	if (access === "team" && !session.hasTeamAccess) return { name: "forbidden" }
	if (access === "hr" && !session.isHr) return { name: "forbidden" }
	return true
})

router.afterEach((to) => {
	document.title = to.meta.title ? `${to.meta.title} · BB HR` : "BB HR"
})
