"""Reporting-manager and HR views.

Managers see the employees below them in the reports_to tree; HR sees everyone.
Salary never appears here - see api/salary.py for that.
"""

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import add_days, cint, date_diff, get_datetime, getdate, now_datetime, today

from bb_academy_hrms.api.attendance import late_minutes, shift_info
from bb_academy_hrms.api.history import parse_range
from bb_academy_hrms.utils import permissions as perm

EMP_FIELDS = [
	"name",
	"employee_name",
	"designation",
	"department",
	"image",
	"holiday_list",
	"company",
	"date_of_joining",
	"reports_to",
]


def _scoped_employees(s, extra_filters=None, fields=None):
	filters = {"status": "Active"}
	if s.employees is not None:
		# a manager's view is about their team, not themself
		team = s.subordinates
		if not team:
			return []
		filters["name"] = ["in", team]
	filters.update(extra_filters or {})
	return frappe.get_all(
		"Employee",
		filters=filters,
		fields=fields or EMP_FIELDS,
		order_by="employee_name asc",
		ignore_permissions=True,
	)


def _holiday_dates(employees, from_date, to_date):
	"""{employee: {date: description}} honouring each employee's own holiday list."""
	from bb_academy_hrms.api.holidays import holiday_list_for

	by_list = defaultdict(list)
	for e in employees:
		by_list[e.holiday_list or holiday_list_for(e.name)].append(e.name)
	out = {}
	for hl, names in by_list.items():
		dates = {}
		if hl:
			for h in frappe.get_all(
				"Holiday",
				filters={"parent": hl, "holiday_date": ["between", [from_date, to_date]]},
				fields=["holiday_date", "description"],
				ignore_permissions=True,
			):
				dates[h.holiday_date] = frappe.utils.strip_html(h.description or "").strip()
		for n in names:
			out[n] = dates
	return out


def _day_rows(employees, date):
	names = [e.name for e in employees]
	if not names:
		return []
	att = {
		a.employee: a
		for a in frappe.get_all(
			"Attendance",
			filters={"employee": ["in", names], "attendance_date": date, "docstatus": 1},
			fields=["employee", "name", "status", "working_hours", "leave_type"],
			ignore_permissions=True,
		)
	}
	logs = defaultdict(list)
	for l in frappe.get_all(
		"Employee Checkin",
		filters={
			"employee": ["in", names],
			"time": ["between", [f"{date} 00:00:00", f"{date} 23:59:59.999999"]],
		},
		fields=["employee", "log_type", "time", "bbhr_office_location"],
		order_by="time asc",
		ignore_permissions=True,
	):
		logs[l.employee].append(l)
	hols = _holiday_dates(employees, date, date)
	is_today = getdate(date) == getdate(today())

	rows = []
	for e in employees:
		a = att.get(e.name)
		ls = logs.get(e.name, [])
		holiday = hols.get(e.name, {}).get(getdate(date))
		if a:
			status = a.status
		elif ls:
			status = "Present"
		elif holiday is not None:
			status = "Holiday"
		else:
			status = "Not Marked"
		first_in = next((l.time for l in ls if l.log_type == "IN"), None)
		late = late_minutes(first_in, shift_info(e.name, first_in)) if first_in else 0
		rows.append(
			{
				"employee": e.name,
				"employee_name": e.employee_name,
				"designation": e.designation,
				"department": e.department,
				"image": e.image,
				"status": status,
				"holiday": holiday,
				"first_in": str(first_in) if first_in else None,
				"last_out": str(ls[-1].time) if ls and ls[-1].log_type == "OUT" else None,
				"currently_in": bool(is_today and ls and ls[-1].log_type == "IN"),
				"punches": len(ls),
				"location": ls[-1].bbhr_office_location if ls else None,
				"late_minutes": late,
				"working_hours": a.working_hours if a else None,
				"leave_type": a.leave_type if a else None,
			}
		)
	return rows


def _summary(rows):
	def n(st):
		return sum(1 for r in rows if r["status"] == st)

	return {
		"total": len(rows),
		"present": n("Present") + n("Work From Home"),
		"half_day": n("Half Day"),
		"on_leave": n("On Leave"),
		"absent": n("Absent"),
		"holiday": n("Holiday"),
		"not_marked": n("Not Marked"),
		"currently_in": sum(1 for r in rows if r["currently_in"]),
		"late": sum(1 for r in rows if r["late_minutes"] > 0),
	}


@frappe.whitelist(methods=["GET"])
def get_team_overview(date=None, department=None, status=None, search=None):
	"""Who is in on `date` across the caller's team (manager) or the whole company (HR)."""
	s = perm.require_team_access()
	date = getdate(date or today())
	if date > getdate(today()):
		frappe.throw(_("Pick today or an earlier date."))
	extra = {"department": department} if department else {}
	employees = _scoped_employees(s, extra)
	rows = _day_rows(employees, date)
	summary = _summary(rows)
	if search:
		q = search.strip().lower()
		rows = [r for r in rows if q in (r["employee_name"] or "").lower() or q in r["employee"].lower()]
	if status:
		rows = [
			r
			for r in rows
			if r["status"] == status
			or (status == "Late" and r["late_minutes"] > 0)
			or (status == "In Now" and r["currently_in"])
		]
	return {"date": str(date), "scope": "company" if s.is_hr else "team", "summary": summary, "rows": rows}


@frappe.whitelist(methods=["GET"])
def get_hr_overview(date=None):
	"""Company-wide numbers for HR: today, a 14-day trend, departments and setup gaps."""
	perm.require_hr()
	s = perm.scope()
	date = getdate(date or today())
	employees = _scoped_employees(s)
	rows = _day_rows(employees, date)

	start = add_days(date, -13)
	names = [e.name for e in employees]
	trend = {add_days(start, i): {"present": 0, "absent": 0, "on_leave": 0} for i in range(14)}
	if names:
		for a in frappe.get_all(
			"Attendance",
			filters={
				"employee": ["in", names],
				"docstatus": 1,
				"attendance_date": ["between", [start, date]],
			},
			fields=["attendance_date", "status"],
			ignore_permissions=True,
		):
			bucket = trend.get(a.attendance_date)
			if not bucket:
				continue
			key = {
				"Present": "present",
				"Work From Home": "present",
				"Half Day": "present",
				"Absent": "absent",
				"On Leave": "on_leave",
			}.get(a.status)
			if key:
				bucket[key] += 1

	departments = defaultdict(lambda: {"total": 0, "present": 0})
	for r in rows:
		d = departments[r["department"] or _("No Department")]
		d["total"] += 1
		if r["status"] in ("Present", "Work From Home", "Half Day"):
			d["present"] += 1

	from bb_academy_hrms.utils.settings import get_settings

	settings = get_settings()
	return {
		"date": str(date),
		"summary": _summary(rows),
		"trend": [{"date": str(k), **v} for k, v in sorted(trend.items())],
		"departments": sorted(
			({"department": k, **v} for k, v in departments.items()), key=lambda d: -d["total"]
		),
		"setup": {
			"employees_without_user": frappe.db.count(
				"Employee", {"status": "Active", "user_id": ["is", "not set"]}
			),
			"employees_without_manager": frappe.db.count(
				"Employee", {"status": "Active", "reports_to": ["is", "not set"]}
			),
			"office_locations": len(settings.office_locations),
			"geofence": bool(settings.enable_geofence),
			"require_photo": bool(settings.require_photo),
		},
	}


@frappe.whitelist(methods=["GET"])
def get_exceptions(from_date=None, to_date=None, kind=None):
	"""Attendance exceptions in the caller's scope: late arrival, missing check-out, unmarked working day."""
	s = perm.require_team_access()
	to_date = min(getdate(to_date or today()), getdate(today()))
	from_date, to_date = parse_range(from_date or add_days(to_date, -6), to_date, max_days=31)
	employees = _scoped_employees(s)
	names = [e.name for e in employees]
	if not names:
		return {"from_date": str(from_date), "to_date": str(to_date), "rows": [], "counts": {}}

	logs = defaultdict(list)
	for l in frappe.get_all(
		"Employee Checkin",
		filters={
			"employee": ["in", names],
			"time": ["between", [f"{from_date} 00:00:00", f"{to_date} 23:59:59.999999"]],
		},
		fields=["employee", "log_type", "time"],
		order_by="time asc",
		ignore_permissions=True,
	):
		logs[(l.employee, getdate(l.time))].append(l)
	att = {
		(a.employee, a.attendance_date): a.status
		for a in frappe.get_all(
			"Attendance",
			filters={
				"employee": ["in", names],
				"docstatus": 1,
				"attendance_date": ["between", [from_date, to_date]],
			},
			fields=["employee", "attendance_date", "status"],
			ignore_permissions=True,
		)
	}
	hols = _holiday_dates(employees, from_date, to_date)
	now = now_datetime()
	current_day = getdate(now)

	rows = []
	for e in employees:
		joined = getdate(e.date_of_joining) if e.date_of_joining else None
		for i in range(date_diff(to_date, from_date) + 1):
			day = add_days(from_date, i)
			if joined and day < joined:
				continue
			ls = logs.get((e.name, day), [])
			base = {
				"employee": e.name,
				"employee_name": e.employee_name,
				"department": e.department,
				"date": str(day),
			}
			if ls:
				first_in = next((l.time for l in ls if l.log_type == "IN"), None)
				late = late_minutes(first_in, shift_info(e.name, first_in)) if first_in else 0
				if late > 0:
					rows.append(
						dict(
							base,
							kind="Late Arrival",
							detail=_("{0} min late").format(late),
							time=str(first_in),
						)
					)
				if ls[-1].log_type == "IN" and day < current_day:
					rows.append(
						dict(
							base,
							kind="Missing Check-out",
							detail=_("Last punch was a check-in"),
							time=str(ls[-1].time),
						)
					)
			elif day < current_day and day not in hols.get(e.name, {}) and (e.name, day) not in att:
				rows.append(
					dict(
						base,
						kind="Not Marked",
						detail=_("No punch or attendance on a working day"),
						time=None,
					)
				)
			elif att.get((e.name, day)) == "Absent":
				rows.append(dict(base, kind="Absent", detail=_("Marked absent"), time=None))

	counts = defaultdict(int)
	for r in rows:
		counts[r["kind"]] += 1
	if kind:
		rows = [r for r in rows if r["kind"] == kind]
	rows.sort(key=lambda r: (r["date"], r["employee_name"] or ""), reverse=True)
	return {
		"from_date": str(from_date),
		"to_date": str(to_date),
		"rows": rows[:500],
		"counts": dict(counts),
		"truncated": len(rows) > 500,
	}


@frappe.whitelist(methods=["GET"])
def get_directory(search=None, department=None, page=1, page_length=30):
	"""Employee directory in the caller's scope. HR additionally sees contact and login details."""
	s = perm.require_team_access()
	fields = ["name", "employee_name", "designation", "department", "image", "reports_to", "date_of_joining"]
	if s.is_hr:
		fields += ["cell_number", "company_email", "user_id"]
	extra = {}
	if department:
		extra["department"] = department
	or_filters = None
	if search:
		like = f"%{search.strip()}%"
		or_filters = {"employee_name": ["like", like], "name": ["like", like], "designation": ["like", like]}

	filters = {"status": "Active", **extra}
	if not s.is_hr:
		if not s.subordinates:
			return {"rows": [], "total": 0, "page": 1, "page_length": cint(page_length)}
		filters["name"] = ["in", s.subordinates]

	page, page_length = max(cint(page), 1), min(max(cint(page_length), 1), 100)
	rows = frappe.get_all(
		"Employee",
		filters=filters,
		or_filters=or_filters,
		fields=fields,
		order_by="employee_name asc",
		start=(page - 1) * page_length,
		page_length=page_length,
		ignore_permissions=True,
	)
	total = len(
		frappe.get_all(
			"Employee", filters=filters, or_filters=or_filters, pluck="name", ignore_permissions=True
		)
	)
	managers = {r.reports_to for r in rows if r.reports_to}
	manager_names = (
		dict(
			frappe.get_all(
				"Employee",
				filters={"name": ["in", list(managers)]},
				fields=["name", "employee_name"],
				as_list=True,
				ignore_permissions=True,
			)
		)
		if managers
		else {}
	)
	for r in rows:
		r["reports_to_name"] = manager_names.get(r.reports_to)
		if s.is_hr:
			r["has_login"] = bool(r.pop("user_id", None))
	return {"rows": rows, "total": total, "page": page, "page_length": page_length, "is_hr": s.is_hr}


@frappe.whitelist(methods=["GET"])
def get_departments():
	s = perm.require_team_access()
	filters = {"status": "Active", "department": ["is", "set"]}
	if not s.is_hr:
		filters["name"] = ["in", s.subordinates or [""]]
	return sorted(
		{d for d in frappe.get_all("Employee", filters=filters, pluck="department", ignore_permissions=True)}
	)
