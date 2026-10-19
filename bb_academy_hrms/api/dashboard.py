"""The employee home screen in one round trip."""

import frappe
from frappe.utils import get_first_day, get_last_day, getdate, today

from bb_academy_hrms.api import attendance, holidays, salary
from bb_academy_hrms.api.history import summarize
from bb_academy_hrms.utils import permissions as perm


def month_summary(employee, ref=None):
	ref = getdate(ref or today())
	start, end = get_first_day(ref), get_last_day(ref)
	rows = frappe.get_all(
		"Attendance",
		filters={"employee": employee, "docstatus": 1, "attendance_date": ["between", [start, end]]},
		fields=["status", "working_hours", "late_entry"],
		ignore_permissions=True,
	)
	upto = min(end, ref)
	hols = holidays.holidays_between(employee, start, upto)
	working_days = (upto - start).days + 1 - len(hols)
	return dict(
		summarize(rows),
		month=start.strftime("%B %Y"),
		working_days_so_far=max(working_days, 0),
		holidays_so_far=len(hols),
	)


def leave_balance(employee):
	"""Totals across leave types from HRMS's own get_leave_details (read only)."""
	from frappe.utils import flt
	from hrms.hr.doctype.leave_application.leave_application import get_leave_details

	try:
		details = get_leave_details(employee, today()).get("leave_allocation") or {}
	except Exception:
		frappe.log_error(title="BB HR: leave balance lookup failed")
		details = {}
	total = sum(flt(d.get("total_leaves")) for d in details.values())
	used = sum(flt(d.get("leaves_taken")) for d in details.values())
	available = sum(flt(d.get("remaining_leaves")) for d in details.values())
	return {
		"total": round(total, 1),
		"used": round(used, 1),
		"available": round(available, 1),
		"types": [
			{
				"leave_type": k,
				"total": flt(v.get("total_leaves")),
				"used": flt(v.get("leaves_taken")),
				"available": flt(v.get("remaining_leaves")),
			}
			for k, v in details.items()
		],
	}


@frappe.whitelist(methods=["GET"])
def get_dashboard():
	emp = perm.require_employee()
	return {
		"today": attendance.get_status(),
		"month": month_summary(emp.name),
		"upcoming_holidays": holidays.upcoming(emp.name, limit=4),
		"recent_slips": salary.recent_slips(emp.name, limit=3),
		"leave_balance": leave_balance(emp.name),
	}
