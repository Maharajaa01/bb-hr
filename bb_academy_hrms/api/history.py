"""Attendance history for one employee (self, or someone in the caller's scope)."""

import frappe
from frappe import _
from frappe.utils import add_days, cint, date_diff, flt, get_first_day, getdate, today

from bb_academy_hrms.utils import permissions as perm

STATUSES = ("Present", "Absent", "Half Day", "On Leave", "Work From Home")
MAX_RANGE_DAYS = 400


def parse_range(from_date=None, to_date=None, max_days=MAX_RANGE_DAYS):
	to_date = getdate(to_date or today())
	from_date = getdate(from_date or get_first_day(to_date))
	if from_date > to_date:
		frappe.throw(_("From date must be before to date."))
	if date_diff(to_date, from_date) > max_days:
		frappe.throw(_("Pick a range of at most {0} days.").format(max_days))
	return from_date, to_date


def summarize(rows):
	counts = {s: 0 for s in STATUSES}
	for r in rows:
		if r.status in counts:
			counts[r.status] += 1
	return {
		"present": counts["Present"] + counts["Work From Home"],
		"absent": counts["Absent"],
		"half_day": counts["Half Day"],
		"on_leave": counts["On Leave"],
		"late": sum(1 for r in rows if r.get("late_entry")),
		"total_hours": round(sum(flt(r.working_hours) for r in rows), 2),
		"marked": len(rows),
	}


@frappe.whitelist(methods=["GET"])
def get_attendance_history(employee=None, from_date=None, to_date=None, status=None, page=1, page_length=20):
	if employee:
		perm.assert_can_view(employee)
	else:
		employee = perm.require_employee().name
	from_date, to_date = parse_range(from_date, to_date)
	if status and status not in STATUSES:
		frappe.throw(_("Unknown status."))

	base = {"employee": employee, "docstatus": 1, "attendance_date": ["between", [from_date, to_date]]}
	filters = dict(base, **({"status": status} if status else {}))
	page, page_length = max(cint(page), 1), min(max(cint(page_length), 1), 100)

	fields = [
		"name",
		"attendance_date",
		"status",
		"working_hours",
		"in_time",
		"out_time",
		"late_entry",
		"early_exit",
		"leave_type",
		"shift",
	]
	rows = frappe.get_all(
		"Attendance",
		filters=filters,
		fields=fields,
		order_by="attendance_date desc",
		start=(page - 1) * page_length,
		page_length=page_length,
		ignore_permissions=True,
	)
	all_rows = frappe.get_all(
		"Attendance", filters=base, fields=["status", "working_hours", "late_entry"], ignore_permissions=True
	)

	# punches for the visible days, so the list can show every IN/OUT of a split shift
	punches = {}
	if rows:
		days = [r.attendance_date for r in rows]
		for log in frappe.get_all(
			"Employee Checkin",
			filters={
				"employee": employee,
				"time": ["between", [f"{min(days)} 00:00:00", f"{max(days)} 23:59:59"]],
			},
			fields=["name", "log_type", "time", "bbhr_office_location", "bbhr_photo"],
			order_by="time asc",
			ignore_permissions=True,
		):
			punches.setdefault(str(getdate(log.time)), []).append(
				{
					"name": log.name,
					"log_type": log.log_type,
					"time": str(log.time),
					"location": log.bbhr_office_location,
					"has_photo": bool(log.bbhr_photo),
				}
			)
	for r in rows:
		r["punches"] = punches.get(str(r.attendance_date), [])

	emp = frappe.db.get_value(
		"Employee", employee, ["employee_name", "designation", "department", "image"], as_dict=True
	)
	return {
		"employee": employee,
		"employee_name": emp.employee_name,
		"designation": emp.designation,
		"department": emp.department,
		"image": emp.image,
		"from_date": str(from_date),
		"to_date": str(to_date),
		"rows": rows,
		"total": frappe.db.count("Attendance", filters),
		"page": page,
		"page_length": page_length,
		"summary": summarize(all_rows),
	}
