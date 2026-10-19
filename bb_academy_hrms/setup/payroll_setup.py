"""Payroll, shift and holiday setup for Black Building Academy.

Source: Staff_Details.xlsx (Posting / Permanent / Internship sheets) shared by the client.
Idempotent - safe to re-run after editing STAFF below:

    bench --site <site> execute bb_academy_hrms.setup.payroll_setup.execute
"""

from datetime import date, timedelta

import frappe
from frappe.utils import getdate

COMPANY = "Black Building Academy"
CURRENCY = "INR"
SALARY_ACCOUNT = "Salary - BBA"
PAYROLL_PAYABLE = "Payroll Payable - BBA"
EFFECTIVE_FROM = date(2026, 10, 1)
YEAR_START, YEAR_END = date(2026, 1, 1), date(2026, 12, 31)
BASE_HOLIDAY_LIST = "BB Academy 2026"  # Sunday weekly off + public holidays (already on site)

# Holiday list keys -> (name, weekdays that are WORKING days; None = every day works)
SUNDAY_OFF = "sunday_off"
NO_WEEKLY_OFF = "no_weekly_off"
SUNDAY_ONLY = "sunday_only"
SATURDAY_ONLY = "saturday_only"
HOLIDAY_LISTS = {
	NO_WEEKLY_OFF: ("BBA 2026 - No Weekly Off", None),
	SUNDAY_ONLY: ("BBA 2026 - Sunday Only Staff", {6}),
	SATURDAY_ONLY: ("BBA 2026 - Saturday Only Staff", {5}),
}

# Salary structures
MONTHLY = "BBA Monthly Salary"
SPLIT = "BBA Monthly Salary - Split Session"
PER_DAY = "BBA Per Day Wages"
STIPEND = "BBA Internship Stipend"

# (employee, structure, base, variable, segments, holiday list, monthly off leave)
# base = monthly salary / per-day rate / monthly stipend. For SPLIT, variable = morning share.
# segments = work timings as (in, out) pairs; the shift spans first-in to last-out.
STAFF = [
	# --- Posting Staff ---
	("HR-EMP-00002", MONTHLY, 30000, 0, [("07:00", "10:15"), ("16:30", "21:45")], SUNDAY_OFF, 0),  # Preethi
	("HR-EMP-00042", MONTHLY, 22000, 0, [("09:15", "12:30"), ("16:45", "22:00")], SUNDAY_OFF, 0),  # Priyadharshini
	("HR-EMP-00003", MONTHLY, 19000, 0, [("06:00", "09:15"), ("16:30", "21:45")], NO_WEEKLY_OFF, 0),  # Snega
	("HR-EMP-00007", MONTHLY, 18000, 0, [("05:45", "07:30"), ("09:45", "11:15"), ("16:30", "21:45")], NO_WEEKLY_OFF, 0),  # Roja
	("HR-EMP-00006", MONTHLY, 18000, 0, [("05:45", "07:45"), ("09:30", "12:30"), ("18:30", "22:00")], NO_WEEKLY_OFF, 1),  # Madhumidha
	("HR-EMP-00008", MONTHLY, 18000, 0, [("05:45", "09:00"), ("16:30", "21:45")], NO_WEEKLY_OFF, 1),  # Saranya
	("HR-EMP-00013", MONTHLY, 12500, 0, [("16:30", "21:30")], NO_WEEKLY_OFF, 1),  # Veeraselvi
	("HR-EMP-00032", MONTHLY, 5000, 0, [("08:45", "12:15")], NO_WEEKLY_OFF, 0),  # Munishgeetha
	("HR-EMP-00010", MONTHLY, 11000, 0, [("17:45", "22:00")], NO_WEEKLY_OFF, 1),  # Logeshwari
	("HR-EMP-00009", MONTHLY, 17000, 0, [("05:45", "08:00"), ("17:00", "22:15")], NO_WEEKLY_OFF, 1),  # Poovizhi
	("HR-EMP-00012", MONTHLY, 11000, 0, [("16:45", "21:45")], NO_WEEKLY_OFF, 1),  # Raghavi
	# --- Permanent Staff: per-day subject teachers ---
	("HR-EMP-00025", PER_DAY, 2000, 0, [("15:00", "18:30")], SUNDAY_ONLY, 0),  # Mageshwari (Physics)
	("HR-EMP-00026", PER_DAY, 2000, 0, [("15:45", "19:15")], SUNDAY_ONLY, 0),  # Geetha (Chemistry)
	("HR-EMP-00027", PER_DAY, 1700, 0, [("16:30", "20:00")], SUNDAY_ONLY, 0),  # Navya (Biology)
	("HR-EMP-00052", PER_DAY, 2000, 0, [("16:30", "20:00")], SUNDAY_ONLY, 0),  # Suganya (C.Sci)
	("HR-EMP-00023", PER_DAY, 1500, 0, [("18:00", "21:30")], SATURDAY_ONLY, 0),  # Sugaranjani (Science)
	("HR-EMP-00018", PER_DAY, 1500, 0, [("18:45", "20:45")], SATURDAY_ONLY, 0),  # Yeshwanthi (Social)
	# HR-EMP-00053 Nathiya (Accounts, Mon & Tue, Rs.1000/day) is skipped: status Left since 2026-09-10.
	# --- Permanent Staff: monthly ---
	("HR-EMP-00011", SPLIT, 11000, 4000, [("05:45", "07:15"), ("18:15", "21:45")], NO_WEEKLY_OFF, 0),  # Anusha: 4000 + 7000
	("HR-EMP-00043", MONTHLY, 8500, 0, [("16:15", "21:15")], NO_WEEKLY_OFF, 0),  # Padmavathy
	("HR-EMP-00014", MONTHLY, 15000, 0, [("18:15", "21:45")], NO_WEEKLY_OFF, 0),  # Sharulakshmi
	("HR-EMP-00017", MONTHLY, 16000, 0, [("06:00", "09:15"), ("16:30", "21:45")], NO_WEEKLY_OFF, 0),  # Sandhiya
	("HR-EMP-00015", MONTHLY, 11000, 0, [("16:30", "21:30")], NO_WEEKLY_OFF, 0),  # Chithra
	("HR-EMP-00022", MONTHLY, 7000, 0, [("18:15", "21:45")], NO_WEEKLY_OFF, 0),  # Sakthi Priya
	("HR-EMP-00016", MONTHLY, 11000, 0, [("16:30", "21:30")], NO_WEEKLY_OFF, 0),  # Krithika R
	("HR-EMP-00033", MONTHLY, 8000, 0, [("06:00", "07:30")], SUNDAY_OFF, 0),  # Vinodhini (figure to verify)
	("HR-EMP-00031", MONTHLY, 4000, 0, [("06:00", "07:30")], NO_WEEKLY_OFF, 0),  # Jeevitha
	("HR-EMP-00054", MONTHLY, 4000, 0, [("06:00", "07:30")], SUNDAY_OFF, 0),  # Monisha
	# --- Internship ---
	("HR-EMP-00038", STIPEND, 5000, 0, [("17:00", "21:30")], NO_WEEKLY_OFF, 0),  # Nivetha
	("HR-EMP-00028", STIPEND, 6500, 0, [("18:00", "21:30")], NO_WEEKLY_OFF, 0),  # Deepika
	("HR-EMP-00030", STIPEND, 7500, 0, [("16:30", "21:30")], NO_WEEKLY_OFF, 0),  # Tamilarasi
	("HR-EMP-00035", STIPEND, 7500, 0, [("16:30", "21:30")], NO_WEEKLY_OFF, 0),  # Kalaiarasi
	("HR-EMP-00029", STIPEND, 7500, 0, [("16:30", "21:30")], NO_WEEKLY_OFF, 0),  # Bouvaneshwari
	("HR-EMP-00034", STIPEND, 9000, 0, [("06:15", "07:45"), ("16:30", "21:30")], SUNDAY_OFF, 0),  # Kreethika
]

COMPONENTS = [
	# name, abbr, depends_on_payment_days
	("Basic", "B", 1),
	("Morning Session Pay", "MSP", 1),
	("Evening Session Pay", "ESP", 1),
	("Daily Wages", "DW", 0),  # already multiplied by payment_days in the formula
	("Stipend", "STP", 1),
]

STRUCTURES = {
	MONTHLY: [("Basic", "base")],
	SPLIT: [("Morning Session Pay", "variable"), ("Evening Session Pay", "base - variable")],
	PER_DAY: [("Daily Wages", "base * payment_days")],
	STIPEND: [("Stipend", "base")],
}

MONTHLY_OFF_LEAVE = "Monthly Off"
MONTHLY_OFF_POLICY = "BBA Monthly Off (1 day / month)"


def execute():
	setup_payroll_settings()
	setup_payroll_period()
	holiday_lists = setup_holiday_lists()
	setup_components()
	setup_structures()
	setup_monthly_off_leave()
	for row in STAFF:
		setup_employee(*row, holiday_lists=holiday_lists)
	frappe.db.commit()
	print(f"Payroll setup complete for {len(STAFF)} employees")


def setup_payroll_settings():
	settings = frappe.get_single("Payroll Settings")
	settings.payroll_based_on = "Attendance"
	settings.consider_unmarked_attendance_as = "Present"
	settings.include_holidays_in_total_working_days = 0
	settings.daily_wages_fraction_for_half_day = 0.5
	settings.save()


def setup_payroll_period():
	name = "FY 2026-2027"
	if not frappe.db.exists("Payroll Period", name):
		frappe.get_doc(
			{
				"doctype": "Payroll Period",
				"name": name,
				"company": COMPANY,
				"start_date": "2026-04-01",
				"end_date": "2027-03-31",
			}
		).insert()


def setup_holiday_lists():
	public = frappe.get_all(
		"Holiday",
		filters={"parent": BASE_HOLIDAY_LIST, "weekly_off": 0},
		fields=["holiday_date", "description"],
	)
	public_dates = {getdate(h.holiday_date): h.description for h in public}
	names = {SUNDAY_OFF: BASE_HOLIDAY_LIST}

	for key, (name, working_weekdays) in HOLIDAY_LISTS.items():
		names[key] = name
		holidays = []
		day = YEAR_START
		while day <= YEAR_END:
			if day in public_dates:
				holidays.append({"holiday_date": day, "description": public_dates[day], "weekly_off": 0})
			elif working_weekdays is not None and day.weekday() not in working_weekdays:
				holidays.append({"holiday_date": day, "description": day.strftime("%A"), "weekly_off": 1})
			day += timedelta(days=1)

		doc = (
			frappe.get_doc("Holiday List", name)
			if frappe.db.exists("Holiday List", name)
			else frappe.new_doc("Holiday List")
		)
		doc.holiday_list_name = name
		doc.from_date, doc.to_date = YEAR_START, YEAR_END
		doc.set("holidays", holidays)
		doc.save()
	return names


def setup_components():
	for name, abbr, depends_on_payment_days in COMPONENTS:
		doc = (
			frappe.get_doc("Salary Component", name)
			if frappe.db.exists("Salary Component", name)
			else frappe.get_doc(
				{"doctype": "Salary Component", "salary_component": name, "salary_component_abbr": abbr}
			)
		)
		doc.type = "Earning"
		doc.depends_on_payment_days = depends_on_payment_days
		if not any(a.company == COMPANY for a in doc.accounts):
			doc.append("accounts", {"company": COMPANY, "account": SALARY_ACCOUNT})
		doc.save()


def setup_structures():
	for name, rows in STRUCTURES.items():
		if frappe.db.exists("Salary Structure", {"name": name, "docstatus": 1}):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Salary Structure",
				"name": name,
				"__newname": name,
				"company": COMPANY,
				"currency": CURRENCY,
				"is_active": "Yes",
				"payroll_frequency": "Monthly",
				"earnings": [
					{"salary_component": component, "amount_based_on_formula": 1, "formula": formula}
					for component, formula in rows
				],
			}
		)
		doc.insert(set_name=name)
		doc.submit()


def setup_monthly_off_leave():
	if not frappe.db.exists("Leave Type", MONTHLY_OFF_LEAVE):
		frappe.get_doc(
			{
				"doctype": "Leave Type",
				"leave_type_name": MONTHLY_OFF_LEAVE,
				"is_earned_leave": 1,
				"earned_leave_frequency": "Monthly",
				"allocate_on_day": "First Day",
				"rounding": "1.0",
				"max_continuous_days_allowed": 1,
				"is_carry_forward": 0,
			}
		).insert()
	if not frappe.db.exists("Leave Policy", {"title": MONTHLY_OFF_POLICY, "docstatus": 1}):
		policy = frappe.get_doc(
			{
				"doctype": "Leave Policy",
				"title": MONTHLY_OFF_POLICY,
				"leave_policy_details": [{"leave_type": MONTHLY_OFF_LEAVE, "annual_allocation": 12}],
			}
		).insert()
		policy.submit()


def shift_type_name(segments):
	return "BBA " + " & ".join(f"{a}-{b}" for a, b in segments)


def setup_shift_type(segments):
	name = shift_type_name(segments)
	minutes = sum(
		(int(b[:2]) * 60 + int(b[3:])) - (int(a[:2]) * 60 + int(a[3:])) for a, b in segments
	)
	is_new = not frappe.db.exists("Shift Type", name)
	doc = frappe.new_doc("Shift Type") if is_new else frappe.get_doc("Shift Type", name)
	doc.update(
		{
			"start_time": segments[0][0] + ":00",
			"end_time": segments[-1][1] + ":00",
			# split shifts: every IN/OUT pair counts, the break between sessions is not worked time
			"determine_check_in_and_check_out": "Alternating entries as IN and OUT during the same shift",
			"working_hours_calculation_based_on": "Every Valid Check-in and Check-out",
			"begin_check_in_before_shift_start_time": 30,
			"allow_check_out_after_shift_end_time": 60,
			"working_hours_threshold_for_half_day": round(minutes / 60 / 2, 2),
			"enable_late_entry_marking": 1,
			"late_entry_grace_period": 15,
			"enable_early_exit_marking": 1,
			"early_exit_grace_period": 15,
			"process_attendance_after": str(EFFECTIVE_FROM),
			"auto_update_last_sync": 1,
		}
	)
	if is_new:
		# switch on from the Shift Type once staff actually check in (device / mobile app),
		# otherwise every assigned employee gets auto-marked Absent
		doc.enable_auto_attendance = 0
		doc.insert(set_name=name)
	else:
		doc.save()
	return name


def setup_employee(employee, structure, base, variable, segments, holiday_key, monthly_off, holiday_lists):
	emp = frappe.get_doc("Employee", employee)
	from_date = max(EFFECTIVE_FROM, getdate(emp.date_of_joining))
	shift = setup_shift_type(segments)

	emp.holiday_list = holiday_lists[holiday_key]
	emp.default_shift = shift
	emp.payroll_cost_center = emp.payroll_cost_center or frappe.db.get_value("Company", COMPANY, "cost_center")
	if structure != PER_DAY:
		emp.ctc = base * 12
		emp.salary_currency = CURRENCY
	emp.save()

	if not frappe.db.exists(
		"Shift Assignment", {"employee": employee, "shift_type": shift, "docstatus": 1, "status": "Active"}
	):
		for old in frappe.get_all(
			"Shift Assignment",
			filters={"employee": employee, "docstatus": 1, "status": "Active", "end_date": ["is", "not set"]},
			pluck="name",
		):
			frappe.db.set_value("Shift Assignment", old, "end_date", from_date - timedelta(days=1))
		frappe.get_doc(
			{
				"doctype": "Shift Assignment",
				"employee": employee,
				"company": COMPANY,
				"shift_type": shift,
				"start_date": from_date,
				"status": "Active",
			}
		).submit()

	existing = frappe.db.get_value(
		"Salary Structure Assignment",
		{"employee": employee, "from_date": from_date, "docstatus": 1},
		["name", "salary_structure", "base", "variable"],
		as_dict=True,
	)
	if existing and (existing.salary_structure, existing.base, existing.variable) != (structure, base, variable):
		frappe.get_doc("Salary Structure Assignment", existing.name).cancel()
		existing = None
	if not existing:
		frappe.get_doc(
			{
				"doctype": "Salary Structure Assignment",
				"employee": employee,
				"salary_structure": structure,
				"company": COMPANY,
				"currency": CURRENCY,
				"from_date": from_date,
				"base": base,
				"variable": variable,
				"payroll_payable_account": PAYROLL_PAYABLE,
			}
		).submit()

	if not monthly_off:
		return
	policy = frappe.db.get_value("Leave Policy", {"title": MONTHLY_OFF_POLICY, "docstatus": 1})
	if not frappe.db.exists(
		"Leave Policy Assignment", {"employee": employee, "leave_policy": policy, "docstatus": 1}
	):
		frappe.get_doc(
			{
				"doctype": "Leave Policy Assignment",
				"employee": employee,
				"company": COMPANY,
				"leave_policy": policy,
				"effective_from": from_date,
				"effective_to": "2027-03-31",
			}
		).submit()
