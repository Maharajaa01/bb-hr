"""Holiday calendar from the employee's assigned Holiday List (falls back to the company default)."""

import frappe
from frappe import _
from frappe.utils import add_days, cint, getdate, today

from bb_academy_hrms.utils import permissions as perm


def holiday_list_for(employee):
	from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

	return get_holiday_list_for_employee(employee, raise_exception=False)


def holidays_between(employee, from_date, to_date, holiday_list=None):
	holiday_list = holiday_list or holiday_list_for(employee)
	if not holiday_list:
		return []
	return frappe.get_all(
		"Holiday",
		filters={"parent": holiday_list, "holiday_date": ["between", [getdate(from_date), getdate(to_date)]]},
		fields=["holiday_date", "description", "weekly_off"],
		order_by="holiday_date asc",
		ignore_permissions=True,
	)


def holiday_on(employee, date):
	rows = holidays_between(employee, date, date)
	if not rows:
		return None
	return {
		"date": str(rows[0].holiday_date),
		"description": _clean(rows[0].description),
		"weekly_off": cint(rows[0].weekly_off),
	}


def upcoming(employee, limit=5, include_weekly_off=False):
	start = getdate(today())
	rows = holidays_between(employee, start, add_days(start, 366))
	if not include_weekly_off:
		rows = [r for r in rows if not r.weekly_off]
	return [_row(r) for r in rows[:limit]]


def _clean(text):
	return frappe.utils.strip_html(text or "").strip()


def _row(r):
	return {
		"date": str(r.holiday_date),
		"description": _clean(r.description),
		"weekly_off": cint(r.weekly_off),
	}


@frappe.whitelist(methods=["GET"])
def get_holidays(year=None, employee=None):
	"""All holidays for a calendar year. `employee` defaults to the caller; others need scope."""
	if employee:
		perm.assert_can_view(employee)
	else:
		employee = perm.require_employee().name
	year = cint(year) or getdate(today()).year
	if year < 2000 or year > 2100:
		frappe.throw(_("Invalid year."))
	holiday_list = holiday_list_for(employee)
	rows = holidays_between(employee, f"{year}-01-01", f"{year}-12-31", holiday_list)
	return {
		"employee": employee,
		"employee_name": frappe.db.get_value("Employee", employee, "employee_name"),
		"holiday_list": holiday_list,
		"year": year,
		"holidays": [_row(r) for r in rows],
		"upcoming": upcoming(employee, limit=5),
	}
