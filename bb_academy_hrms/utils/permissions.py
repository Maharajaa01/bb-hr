"""Who is asking, and which employees may they see?

Every BB HR endpoint resolves scope here, server side. The UI hides what a
user cannot open, but the checks in this module are what actually enforce it.

Scopes
  * Employee          - their own records only.
  * Reporting Manager - anyone below them in the Employee `reports_to` tree
                        (attendance, holidays, directory). Never salary.
  * HR administrator  - HR Manager, HR User or System Manager: every employee,
                        including salary slips.
"""

import frappe
from frappe import _

HR_ROLES = ("HR Manager", "HR User", "System Manager")


def is_hr(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return bool(set(frappe.get_roles(user)) & set(HR_ROLES))


def get_employee_for_user(user=None):
	"""The Employee record linked to this user, or None. Active employees win over others."""
	user = user or frappe.session.user
	if not user or user == "Guest":
		return None
	rows = frappe.get_all(
		"Employee",
		filters={"user_id": user, "status": ["!=", "Left"]},
		fields=[
			"name",
			"employee_name",
			"first_name",
			"designation",
			"department",
			"company",
			"image",
			"status",
			"holiday_list",
			"default_shift",
			"date_of_joining",
			"reports_to",
			"lft",
			"rgt",
		],
		order_by="creation asc",
		ignore_permissions=True,
	)
	active = [r for r in rows if r.status == "Active"]
	return (active or rows or [None])[0]


def require_employee(user=None):
	emp = get_employee_for_user(user)
	if not emp:
		frappe.throw(
			_(
				"Your login is not linked to an employee record. Ask HR to set your user on your Employee profile."
			),
			title=_("No Employee Record"),
			exc=frappe.PermissionError,
		)
	if emp.status != "Active":
		frappe.throw(
			_("Your employee record is {0}. Only active employees can use this.").format(emp.status),
			title=_("Inactive Employee"),
			exc=frappe.PermissionError,
		)
	return emp


def get_subordinates(employee):
	"""Every employee below `employee` in the reports_to tree (direct and indirect)."""
	if not employee:
		return []
	row = frappe.db.get_value("Employee", employee, ["lft", "rgt"], as_dict=True)
	if not row or not row.lft or not row.rgt or row.rgt - row.lft <= 1:
		# fall back to direct reports if the nested set has not been rebuilt
		return frappe.get_all(
			"Employee", filters={"reports_to": employee}, pluck="name", ignore_permissions=True
		)
	return frappe.get_all(
		"Employee",
		filters={"lft": [">", row.lft], "rgt": ["<", row.rgt]},
		pluck="name",
		ignore_permissions=True,
	)


def is_manager(user=None):
	emp = get_employee_for_user(user)
	return bool(emp and frappe.db.exists("Employee", {"reports_to": emp.name, "status": "Active"}))


def scope(user=None):
	"""Describe what this user may see. `employees` is None for HR (meaning: everyone)."""
	user = user or frappe.session.user
	emp = get_employee_for_user(user)
	hr = is_hr(user)
	subordinates = [] if hr or not emp else get_subordinates(emp.name)
	return frappe._dict(
		user=user,
		employee=emp,
		is_hr=hr,
		is_manager=bool(subordinates) or (hr and bool(emp) and is_manager(user)),
		subordinates=subordinates,
		employees=None if hr else ([emp.name] if emp else []) + subordinates,
	)


def visible_employees(user=None):
	"""List of employee ids this user may view, or None meaning 'all' (HR)."""
	return scope(user).employees


def assert_can_view(employee, user=None, salary=False):
	"""Throw PermissionError unless `user` may see `employee`'s records.

	Salary data is stricter: only the employee themself or HR.
	"""
	if not employee or not frappe.db.exists("Employee", employee):
		frappe.throw(_("Employee not found."), frappe.DoesNotExistError)
	s = scope(user)
	if s.is_hr:
		return s
	own = s.employee and s.employee.name == employee
	if salary:
		if own:
			return s
	elif own or employee in s.subordinates:
		return s
	frappe.throw(_("You are not allowed to view this employee's records."), frappe.PermissionError)


def require_hr(user=None):
	if not is_hr(user):
		frappe.throw(_("Only HR can do this."), frappe.PermissionError)


def require_team_access(user=None):
	"""Managers and HR only. Returns the scope."""
	s = scope(user)
	if not (s.is_hr or s.subordinates):
		frappe.throw(_("This view is for reporting managers and HR."), frappe.PermissionError)
	return s
