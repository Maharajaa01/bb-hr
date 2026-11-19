"""Shift planner (HR only): shift timings and who works them.

A "shift" is an HRMS Shift Type (start/end time); an allocation is a submitted
Shift Assignment (employee + shift type + date range). An employee may hold several
shifts at once (a morning and an evening class, say) as long as their timings never
overlap on a day both are in force. That rule is checked here, before HRMS's own
(less strict) check, so the planner can show every conflict at once.

Times travel as "HH:MM" (24 h). A shift whose end is not after its start runs
past midnight.
"""

import re
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import add_days, getdate, today

from bb_academy_hrms.utils import permissions as perm

TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)(:\d\d)?$")
DAY = 24 * 60
NAME_PREFIX = "BBA"  # matches the academy's existing "BBA 06:00-07:30" shift names


# ------------------------------------------------------------------ helpers
def to_minutes(value):
	"""Minutes after midnight for a timedelta (as MariaDB returns Time) or "HH:MM[:SS]"."""
	if isinstance(value, timedelta):
		return int(value.total_seconds() // 60) % DAY
	m = TIME_RE.match(str(value or "").strip())
	if not m:
		frappe.throw(_("Times must look like 09:30."), frappe.ValidationError)
	return int(m.group(1)) * 60 + int(m.group(2))


def hhmm(minutes):
	return f"{minutes // 60 % 24:02d}:{minutes % 60:02d}"


def span(start, end):
	"""(start, end) in minutes with end > start; overnight shifts end after 1440."""
	return (start, end + DAY if end <= start else end)


def times_overlap(a, b):
	"""Do two daily shifts (start, end minutes) overlap? Overnight parts spill into the next day."""
	a, b = span(*a), span(*b)
	return any(a[0] < b[1] + d and b[0] + d < a[1] for d in (-DAY, 0, DAY))


def dates_overlap(a_from, a_to, b_from, b_to):
	a_from, b_from = getdate(a_from), getdate(b_from)
	a_to = getdate(a_to) if a_to else None
	b_to = getdate(b_to) if b_to else None
	return (a_to is None or a_to >= b_from) and (b_to is None or b_to >= a_from)


def _shift_types():
	return {
		t.name: frappe._dict(name=t.name, start=to_minutes(t.start_time), end=to_minutes(t.end_time))
		for t in frappe.get_all("Shift Type", fields=["name", "start_time", "end_time"], ignore_permissions=True)
	}


def _assignments(employees=None, include_past=False):
	filters = {"docstatus": 1, "status": "Active"}
	if employees is not None:
		filters["employee"] = ["in", list(employees) or [""]]
	rows = frappe.get_all(
		"Shift Assignment",
		filters=filters,
		fields=["name", "employee", "shift_type", "start_date", "end_date"],
		order_by="start_date asc",
		ignore_permissions=True,
	)
	if include_past:
		return rows
	t = getdate(today())
	return [r for r in rows if not r.end_date or getdate(r.end_date) >= t]


def find_conflicts(employee, start, end, from_date, to_date, exclude=(), types=None, existing=None):
	"""Existing allocations of `employee` that clash with a new start/end over from..to."""
	types = types or _shift_types()
	rows = existing if existing is not None else _assignments([employee], include_past=True)
	out = []
	for r in rows:
		if r.employee != employee or r.name in exclude:
			continue
		st = types.get(r.shift_type)
		if not st or not dates_overlap(from_date, to_date, r.start_date, r.end_date):
			continue
		if times_overlap((start, end), (st.start, st.end)):
			out.append(
				{
					"assignment": r.name,
					"shift_type": r.shift_type,
					"start": hhmm(st.start),
					"end": hhmm(st.end),
					"from_date": str(r.start_date),
					"to_date": str(r.end_date) if r.end_date else None,
				}
			)
	return out


def _validate_window(start, end, from_date, to_date):
	if start == end:
		frappe.throw(_("Start and end time cannot be the same."), title=_("Check the Timing"))
	if not from_date:
		frappe.throw(_("Choose the date the shift starts from."), title=_("Start Date Needed"))
	if to_date and getdate(to_date) < getdate(from_date):
		frappe.throw(_("The end date is before the start date."), title=_("Check the Dates"))


def ensure_shift_type(start, end, shift_name=None, types=None):
	"""Reuse the shift type with exactly these times, or create one."""
	types = types or _shift_types()
	shift_name = (shift_name or "").strip()
	if shift_name and shift_name in types:
		st = types[shift_name]
		if (st.start, st.end) == (start, end):
			return shift_name
		frappe.throw(
			_("A shift named {0} already exists with different timings ({1} - {2}). Choose another name.").format(
				frappe.bold(shift_name), hhmm(st.start), hhmm(st.end)
			),
			title=_("Name Taken"),
		)
	if not shift_name:
		same = [t.name for t in types.values() if (t.start, t.end) == (start, end)]
		if same:
			return sorted(same, key=len)[0]
		shift_name = f"{NAME_PREFIX} {hhmm(start)}-{hhmm(end)}"
		n = 2
		while shift_name in types:
			shift_name = f"{NAME_PREFIX} {hhmm(start)}-{hhmm(end)} ({n})"
			n += 1
	doc = frappe.new_doc("Shift Type")
	doc.name = shift_name
	doc.start_time = hhmm(start) + ":00"
	doc.end_time = hhmm(end) + ":00"
	doc.flags.ignore_permissions = True
	doc.insert(set_name=shift_name)
	return doc.name


def _allow_multiple_shifts():
	"""HRMS refuses a second shift on the same date unless this HR setting is on."""
	if not frappe.db.get_single_value("HR Settings", "allow_multiple_shift_assignments"):
		frappe.db.set_single_value("HR Settings", "allow_multiple_shift_assignments", 1)
		return True
	return False


def _new_assignment(emp, shift_type, from_date, to_date):
	doc = frappe.new_doc("Shift Assignment")
	doc.employee = emp.name
	doc.employee_name = emp.employee_name
	doc.department = emp.department
	doc.company = emp.company
	doc.shift_type = shift_type
	doc.start_date = getdate(from_date)
	doc.end_date = getdate(to_date) if to_date else None
	doc.status = "Active"
	doc.flags.ignore_permissions = True
	previous = frappe.flags.mute_messages
	frappe.flags.mute_messages = True  # HRMS's "already has a shift on these dates" warning
	try:
		doc.insert()
		doc.submit()
	finally:
		frappe.flags.mute_messages = previous
	return doc.name


def _employee(name):
	emp = frappe.db.get_value(
		"Employee", name, ["name", "employee_name", "department", "company", "status"], as_dict=True
	)
	if not emp:
		frappe.throw(_("Employee {0} not found.").format(name), frappe.DoesNotExistError)
	if emp.status != "Active":
		frappe.throw(_("{0} is not an active employee.").format(emp.employee_name))
	return emp


def _parse_list(value):
	if isinstance(value, str):
		value = frappe.parse_json(value)
	return [v for v in (value or []) if v]


# ---------------------------------------------------------------- endpoints
@frappe.whitelist(methods=["GET"])
def get_planner():
	"""Employees with their current and upcoming shifts, and every shift timing."""
	perm.require_hr()
	types = _shift_types()
	employees = frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		fields=["name", "employee_name", "designation", "department", "image"],
		order_by="employee_name asc",
		ignore_permissions=True,
	)
	by_emp = {}
	for a in _assignments([e.name for e in employees]):
		st = types.get(a.shift_type)
		if not st:
			continue
		by_emp.setdefault(a.employee, []).append(
			{
				"assignment": a.name,
				"shift_type": a.shift_type,
				"start": hhmm(st.start),
				"end": hhmm(st.end),
				"from_date": str(a.start_date),
				"to_date": str(a.end_date) if a.end_date else None,
			}
		)
	usage = {}
	for e in employees:
		e.shifts = sorted(by_emp.get(e.name, []), key=lambda s: (s["start"], s["from_date"]))
		for s in e.shifts:
			usage.setdefault(s["shift_type"], set()).add(e.name)

	return {
		"today": today(),
		"employees": employees,
		"shift_types": sorted(
			[
				{
					"name": t.name,
					"start": hhmm(t.start),
					"end": hhmm(t.end),
					"employees": sorted(usage.get(t.name, ())),
				}
				for t in types.values()
			],
			key=lambda t: (t["start"], t["end"], t["name"]),
		),
		"departments": sorted({e.department for e in employees if e.department}),
		"multiple_allowed": bool(frappe.db.get_single_value("HR Settings", "allow_multiple_shift_assignments")),
	}


@frappe.whitelist(methods=["POST"])
def allocate(employees, from_date, to_date=None, shift_type=None, start_time=None, end_time=None, shift_name=None):
	"""Give one shift to several employees. Nothing is saved if any of them would clash."""
	perm.require_hr()
	names = list(dict.fromkeys(_parse_list(employees)))
	if not names:
		frappe.throw(_("Select at least one employee."), title=_("No Employees"))
	types = _shift_types()
	if shift_type:
		if shift_type not in types:
			frappe.throw(_("Shift {0} not found.").format(shift_type), frappe.DoesNotExistError)
		start, end = types[shift_type].start, types[shift_type].end
	else:
		start, end = to_minutes(start_time), to_minutes(end_time)
	to_date = to_date or None
	_validate_window(start, end, from_date, to_date)

	emps = [_employee(n) for n in names]
	existing = _assignments(names, include_past=True)
	conflicts = []
	for emp in emps:
		clash = find_conflicts(emp.name, start, end, from_date, to_date, types=types, existing=existing)
		if clash:
			conflicts.append({"employee": emp.name, "employee_name": emp.employee_name, "conflicts": clash})
	if conflicts:
		return {"ok": False, "conflicts": conflicts}

	shift_type = shift_type or ensure_shift_type(start, end, shift_name, types)
	enabled = False
	if any(dates_overlap(from_date, to_date, r.start_date, r.end_date) for r in existing):
		enabled = _allow_multiple_shifts()
	created = [_new_assignment(emp, shift_type, from_date, to_date) for emp in emps]
	return {"ok": True, "created": len(created), "shift_type": shift_type, "enabled_multiple": enabled}


@frappe.whitelist(methods=["POST"])
def update_assignment(assignment, start_time, end_time, from_date, to_date=None):
	"""Change one employee's shift timing and/or dates.

	Past days keep the timing they were worked under: when the timing of a shift that has
	already started changes, the old allocation ends yesterday and the new one runs from today.
	"""
	perm.require_hr()
	old = frappe.get_doc("Shift Assignment", assignment)
	if old.docstatus != 1 or old.status != "Active":
		frappe.throw(_("This shift allocation is no longer active. Reload the page."))
	types = _shift_types()
	start, end = to_minutes(start_time), to_minutes(end_time)
	to_date = to_date or None
	current = types.get(old.shift_type)
	timing_changed = not current or (current.start, current.end) != (start, end)
	t = getdate(today())
	started = getdate(old.start_date) <= t
	if started and getdate(from_date) != getdate(old.start_date):
		from_date = old.start_date  # the start of a running shift is history
	new_from = t if (started and timing_changed) else getdate(from_date)
	_validate_window(start, end, new_from, to_date)
	if to_date and getdate(to_date) < t and timing_changed:
		frappe.throw(_("The end date is in the past. A new timing can only apply from today on."))

	clash = find_conflicts(old.employee, start, end, new_from, to_date, exclude={old.name}, types=types)
	if clash:
		return {"ok": False, "conflicts": [{"employee": old.employee, "employee_name": old.employee_name, "conflicts": clash}]}

	if not timing_changed and getdate(from_date) == getdate(old.start_date):
		old.end_date = getdate(to_date) if to_date else None
		old.flags.ignore_permissions = True
		old.save()
		return {"ok": True, "assignment": old.name, "message": _("Dates updated.")}

	shift_type = ensure_shift_type(start, end, types=types) if timing_changed else old.shift_type
	if started and getdate(old.start_date) < t:
		old.end_date = add_days(t, -1)
		message = _("New timing applies from today; earlier days keep the old timing.")
	else:
		old.status = "Inactive"
		message = _("Shift updated.")
	old.flags.ignore_permissions = True
	old.save()
	others = [r for r in _assignments([old.employee], include_past=True) if r.name != old.name]
	if any(dates_overlap(new_from, to_date, r.start_date, r.end_date) for r in others):
		_allow_multiple_shifts()
	name = _new_assignment(_employee(old.employee), shift_type, new_from, to_date)
	return {"ok": True, "assignment": name, "shift_type": shift_type, "message": message}


@frappe.whitelist(methods=["POST"])
def end_assignment(assignment):
	"""Take a shift away from an employee from today on (earlier days are kept)."""
	perm.require_hr()
	doc = frappe.get_doc("Shift Assignment", assignment)
	if doc.docstatus != 1 or doc.status != "Active":
		frappe.throw(_("This shift allocation is no longer active. Reload the page."))
	t = getdate(today())
	if getdate(doc.start_date) < t:
		doc.end_date = add_days(t, -1)
	else:
		doc.status = "Inactive"
	doc.flags.ignore_permissions = True
	doc.save()
	return {"ok": True}


@frappe.whitelist(methods=["POST"])
def save_shift_type(start_time, end_time, name=None, shift_name=None):
	"""Create a shift timing, or change the timing of an existing one for everyone on it."""
	perm.require_hr()
	start, end = to_minutes(start_time), to_minutes(end_time)
	if start == end:
		frappe.throw(_("Start and end time cannot be the same."), title=_("Check the Timing"))
	types = _shift_types()

	if not name:
		if shift_name and shift_name.strip() in types:
			frappe.throw(_("A shift named {0} already exists.").format(frappe.bold(shift_name)), title=_("Name Taken"))
		return {"ok": True, "name": ensure_shift_type(start, end, shift_name or None, types)}

	if name not in types:
		frappe.throw(_("Shift {0} not found.").format(name), frappe.DoesNotExistError)
	on_it = [a for a in _assignments() if a.shift_type == name]
	others = _assignments({a.employee for a in on_it}, include_past=True)
	conflicts = []
	for a in on_it:
		clash = find_conflicts(
			a.employee, start, end, a.start_date, a.end_date, exclude={a.name}, types=types, existing=others
		)
		if clash:
			conflicts.append(
				{
					"employee": a.employee,
					"employee_name": frappe.db.get_value("Employee", a.employee, "employee_name"),
					"conflicts": clash,
				}
			)
	if conflicts:
		return {"ok": False, "conflicts": conflicts}

	doc = frappe.get_doc("Shift Type", name)
	doc.start_time = hhmm(start) + ":00"
	doc.end_time = hhmm(end) + ":00"
	doc.flags.ignore_permissions = True
	doc.save()
	return {"ok": True, "name": doc.name}
