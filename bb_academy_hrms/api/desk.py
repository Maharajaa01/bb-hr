"""Data for the Desk workspaces "BB HR" (HR) and "My HR" (employee).

Number Cards of type Custom and Dashboard Chart Sources call these. Every
function checks scope first. Chart sources deliberately do NOT use
frappe.utils.dashboard.cache_source: it caches by chart name for all users and
returns the cached value before the function body runs, which would hand one
employee's numbers (or HR-wide numbers) to whoever opens the chart next.
"""

import frappe
from frappe import _
from frappe.utils import add_days, add_months, flt, get_first_day, get_last_day, getdate, today

from bb_academy_hrms.api import attendance as att_api
from bb_academy_hrms.api import holidays as hol_api
from bb_academy_hrms.api import salary as sal_api
from bb_academy_hrms.api.dashboard import month_summary
from bb_academy_hrms.api.team import _day_rows, _scoped_employees, _summary
from bb_academy_hrms.utils import permissions as perm

BLUE = "#0284C7"


def _card(value, fieldtype="Int", route=None, route_options=None, **extra):
	out = {"value": value, "fieldtype": fieldtype}
	if route:
		out["route"] = route
	if route_options:
		out["route_options"] = route_options
	out.update(extra)
	return out


# ---------------------------------------------------------------- HR cards
def _today_summary():
	perm.require_hr()
	s = perm.scope()
	return _summary(_day_rows(_scoped_employees(s), getdate(today())))


@frappe.whitelist()
def hr_present_today(filters=None):
	s = _today_summary()
	return _card(
		s["present"] + s["half_day"],
		route=["List", "Attendance"],
		route_options={"attendance_date": today(), "docstatus": 1},
	)


@frappe.whitelist()
def hr_in_now(filters=None):
	return _card(
		_today_summary()["currently_in"],
		route=["List", "Employee Checkin"],
		route_options={"time": [">=", today()]},
	)


@frappe.whitelist()
def hr_not_marked_today(filters=None):
	return _card(_today_summary()["not_marked"])


@frappe.whitelist()
def hr_late_today(filters=None):
	return _card(_today_summary()["late"])


@frappe.whitelist()
def hr_on_leave_today(filters=None):
	return _card(
		_today_summary()["on_leave"],
		route=["List", "Attendance"],
		route_options={"attendance_date": today(), "status": "On Leave"},
	)


@frappe.whitelist()
def hr_without_login(filters=None):
	perm.require_hr()
	n = frappe.db.count("Employee", {"status": "Active", "user_id": ["is", "not set"]})
	return _card(
		n, route=["List", "Employee"], route_options={"status": "Active", "user_id": ["is", "not set"]}
	)


# ----------------------------------------------------------- employee cards
@frappe.whitelist()
def my_today(filters=None):
	"""Today's state as text, e.g. 'In since 9:05 AM'."""
	emp = perm.require_employee()
	logs = att_api.day_logs(emp.name, getdate(today()))
	if not logs:
		holiday = hol_api.holiday_on(emp.name, today())
		text = (
			_("Holiday")
			if holiday and not holiday["weekly_off"]
			else _("Weekly off")
			if holiday
			else _("Not checked in")
		)
	elif logs[-1].log_type == "IN":
		text = _("In since {0}").format(
			frappe.utils.get_datetime(logs[0].time).strftime("%I:%M %p").lstrip("0")
		)
	else:
		text = _("Out at {0}").format(
			frappe.utils.get_datetime(logs[-1].time).strftime("%I:%M %p").lstrip("0")
		)
	return text


@frappe.whitelist()
def my_present_this_month(filters=None):
	emp = perm.require_employee()
	return _card(month_summary(emp.name)["present"])


@frappe.whitelist()
def my_absent_this_month(filters=None):
	emp = perm.require_employee()
	m = month_summary(emp.name)
	return _card(m["absent"])


@frappe.whitelist()
def my_hours_this_month(filters=None):
	emp = perm.require_employee()
	return _card(flt(month_summary(emp.name)["total_hours"], 1), fieldtype="Float")


@frappe.whitelist()
def my_last_net_pay(filters=None):
	emp = perm.require_employee()
	slips = sal_api.recent_slips(emp.name, limit=1)
	if not slips:
		return _("No slip yet")
	s = slips[0]
	return _card(
		flt(s.rounded_total or s.net_pay),
		fieldtype="Currency",
		route=["Form", "Salary Slip", s.name]
		if frappe.has_permission("Salary Slip", "read", s.name)
		else None,
	)


@frappe.whitelist()
def my_next_holiday(filters=None):
	emp = perm.require_employee()
	nxt = hol_api.upcoming(emp.name, limit=1)
	if not nxt:
		return _("None scheduled")
	return f"{getdate(nxt[0]['date']).strftime('%d %b')} · {nxt[0]['description']}"


# ----------------------------------------------------------- chart sources
def hr_attendance_trend(days=30):
	"""Present / absent / on leave per day for the last `days` days (HR only)."""
	perm.require_hr()
	end = getdate(today())
	start = add_days(end, -(days - 1))
	rows = frappe.get_all(
		"Attendance",
		filters={"docstatus": 1, "attendance_date": ["between", [start, end]]},
		fields=["attendance_date", "status", "count(name) as n"],
		group_by="attendance_date, status",
		ignore_permissions=True,
	)
	keys = [add_days(start, i) for i in range(days)]
	series = {"Present": [0] * days, "Absent": [0] * days, "On Leave": [0] * days}
	for r in rows:
		bucket = "Present" if r.status in ("Present", "Half Day", "Work From Home") else r.status
		if bucket in series:
			series[bucket][(getdate(r.attendance_date) - start).days] += r.n
	return {
		"labels": [d.strftime("%d %b") for d in keys],
		"datasets": [{"name": _(k), "values": v} for k, v in series.items()],
	}


def hr_department_today():
	perm.require_hr()
	s = perm.scope()
	rows = _day_rows(_scoped_employees(s), getdate(today()))
	agg = {}
	for r in rows:
		d = (r["department"] or _("No Department")).replace(" - BBA", "")
		a = agg.setdefault(d, [0, 0])
		a[0] += 1
		if r["status"] in ("Present", "Half Day", "Work From Home"):
			a[1] += 1
	names = sorted(agg, key=lambda k: -agg[k][0])
	return {
		"labels": names,
		"datasets": [
			{"name": _("Present"), "values": [agg[k][1] for k in names]},
			{"name": _("Not present"), "values": [agg[k][0] - agg[k][1] for k in names]},
		],
	}


def my_attendance_months(months=6):
	"""The caller's own present / absent / leave counts for the last `months` months."""
	emp = perm.require_employee()
	first = get_first_day(add_months(today(), -(months - 1)))
	last = get_last_day(today())
	rows = frappe.get_all(
		"Attendance",
		filters={"employee": emp.name, "docstatus": 1, "attendance_date": ["between", [first, last]]},
		fields=["attendance_date", "status"],
		ignore_permissions=True,
	)
	labels, keys = [], []
	for i in range(months):
		d = add_months(first, i)
		keys.append((d.year, d.month))
		labels.append(d.strftime("%b %Y"))
	series = {"Present": [0] * months, "Absent": [0] * months, "On Leave": [0] * months}
	for r in rows:
		d = getdate(r.attendance_date)
		idx = keys.index((d.year, d.month))
		bucket = "Present" if r.status in ("Present", "Half Day", "Work From Home") else r.status
		if bucket in series:
			series[bucket][idx] += 1
	return {"labels": labels, "datasets": [{"name": _(k), "values": v} for k, v in series.items()]}
