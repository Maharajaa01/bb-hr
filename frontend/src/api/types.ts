export interface SessionInfo {
	user: { name: string; full_name: string; image: string | null } | null
	employee: {
		name: string
		employee_name: string
		first_name: string | null
		designation: string | null
		department: string | null
		company: string
		image: string | null
		status: string
		date_of_joining: string | null
	} | null
	roles?: { is_employee: boolean; is_manager: boolean; is_hr: boolean; team_size: number | null }
	today?: string
	desk_access?: boolean
}

export interface PunchLog {
	name: string
	log_type: "IN" | "OUT"
	time: string
	location: string | null
	distance: number | null
}

export interface OfficeLocation {
	name: string
	latitude: number
	longitude: number
	radius: number
}

export interface Holiday {
	date: string
	description: string
	weekly_off: number
}

export interface AttendanceStatus {
	employee: string
	employee_name: string
	date: string
	server_time: string
	logs: PunchLog[]
	checked_in: boolean
	next_action: "IN" | "OUT"
	first_in: string | null
	last_out: string | null
	worked_hours: number
	late_minutes: number
	shift: { name?: string; start?: string; end?: string; grace_minutes?: number }
	holiday: Holiday | null
	attendance: { name: string; status: string; working_hours: number; in_time: string | null; out_time: string | null; leave_type: string | null } | null
	rules: {
		geofence: boolean
		require_photo: boolean
		max_accuracy: number
		accuracy_tolerance: number
		min_gap_seconds: number
		locations: OfficeLocation[]
	}
}

export interface PunchResult {
	ok: boolean
	replayed: boolean
	checkin: string
	log_type: "IN" | "OUT"
	time: string
	location: string | null
	distance: number | null
	attendance: string | null
	warning: string | null
	message: string
}

export interface Summary {
	present: number
	absent: number
	half_day: number
	on_leave: number
	late: number
	total_hours: number
	marked: number
}

export interface SalarySlipRow {
	name: string
	employee: string
	employee_name: string
	start_date: string
	end_date: string
	posting_date: string
	currency: string
	gross_pay: number
	total_deduction: number
	net_pay: number
	rounded_total: number
	payment_days: number
	total_working_days: number
	salary_structure: string
}

export interface Dashboard {
	today: AttendanceStatus
	month: Summary & { month: string; working_days_so_far: number; holidays_so_far: number }
	upcoming_holidays: Holiday[]
	recent_slips: SalarySlipRow[]
	leave_balance: LeaveBalance
}

export interface LeaveBalance {
	total: number
	used: number
	available: number
	types: { leave_type: string; total: number; used: number; available: number }[]
}

export interface HistoryPunch {
	name: string
	log_type: "IN" | "OUT"
	time: string
	location: string | null
	has_photo: boolean
}

export interface AttendanceRow {
	name: string
	attendance_date: string
	status: string
	working_hours: number
	in_time: string | null
	out_time: string | null
	late_entry: number
	early_exit: number
	leave_type: string | null
	shift: string | null
	punches: HistoryPunch[]
}

export interface AttendanceHistory {
	employee: string
	employee_name: string
	designation: string | null
	department: string | null
	image: string | null
	from_date: string
	to_date: string
	rows: AttendanceRow[]
	total: number
	page: number
	page_length: number
	summary: Summary
}

export interface SalarySlipList {
	employee: string
	employee_name: string
	rows: SalarySlipRow[]
	total: number
	page: number
	page_length: number
	years: number[]
}

export interface SalaryLine {
	component: string
	abbr: string
	amount: number
}

export interface SalarySlipDetail {
	name: string
	employee: string
	employee_name: string
	designation: string | null
	department: string | null
	company: string
	start_date: string
	end_date: string
	posting_date: string
	currency: string
	salary_structure: string
	payroll_frequency: string
	total_working_days: number
	payment_days: number
	absent_days: number
	leave_without_pay: number
	earnings: SalaryLine[]
	deductions: SalaryLine[]
	gross_pay: number
	total_deduction: number
	net_pay: number
	rounded_total: number
	total_in_words: string | null
	bank_name: string | null
	bank_account_no: string | null
}

export interface HolidayCalendar {
	employee: string
	employee_name: string
	holiday_list: string | null
	year: number
	holidays: Holiday[]
	upcoming: Holiday[]
}

export interface TeamRow {
	employee: string
	employee_name: string
	designation: string | null
	department: string | null
	image: string | null
	status: string
	holiday: string | null
	first_in: string | null
	last_out: string | null
	currently_in: boolean
	punches: number
	location: string | null
	late_minutes: number
	working_hours: number | null
	leave_type: string | null
}

export interface TeamSummary {
	total: number
	present: number
	half_day: number
	on_leave: number
	absent: number
	holiday: number
	not_marked: number
	currently_in: number
	late: number
}

export interface TeamOverview {
	date: string
	scope: "team" | "company"
	summary: TeamSummary
	rows: TeamRow[]
}

export interface HrOverview {
	date: string
	summary: TeamSummary
	trend: { date: string; present: number; absent: number; on_leave: number }[]
	departments: { department: string; total: number; present: number }[]
	setup: {
		employees_without_user: number
		employees_without_manager: number
		office_locations: number
		geofence: boolean
		require_photo: boolean
	}
}

export interface ExceptionRow {
	employee: string
	employee_name: string
	department: string | null
	date: string
	kind: "Late Arrival" | "Missing Check-out" | "Not Marked" | "Absent"
	detail: string
	time: string | null
}

export interface ExceptionReport {
	from_date: string
	to_date: string
	rows: ExceptionRow[]
	counts: Record<string, number>
	truncated?: boolean
}

export interface DirectoryRow {
	name: string
	employee_name: string
	designation: string | null
	department: string | null
	image: string | null
	reports_to: string | null
	reports_to_name: string | null
	date_of_joining: string | null
	cell_number?: string | null
	company_email?: string | null
	has_login?: boolean
}

export interface Directory {
	rows: DirectoryRow[]
	total: number
	page: number
	page_length: number
	is_hr?: boolean
}
