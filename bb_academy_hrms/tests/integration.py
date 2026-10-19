"""BB HR integration checks against a real site - nothing is ever committed.

    bench --site <site> execute bb_academy_hrms.tests.integration.run

Everything runs inside one transaction that is rolled back at the end;
frappe.db.commit is patched to raise, so a stray commit fails the run instead
of leaving test data behind. Needs at least two active employees with
submitted salary slips for one of them (true on the BB Academy site).
"""

import base64
import time
import traceback

import frappe
from frappe.utils import add_days, getdate, today

from bb_academy_hrms.utils.geo import haversine_distance

OFFICE = (11.0168, 76.9558)  # any fixed point; the test office is created inside the transaction


def _jpeg():
	from io import BytesIO

	from PIL import Image

	buf = BytesIO()
	Image.new("RGB", (32, 32), (200, 160, 40)).save(buf, "JPEG")
	return buf.getvalue()


PHOTO = "data:image/jpeg;base64," + base64.b64encode(_jpeg()).decode()
CORRUPT = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff\xe0" + b"\x00" * 64).decode()


class Fail(AssertionError):
	pass


def check(cond, msg):
	if not cond:
		raise Fail(msg)


def raises(exc, fn, *a, contains=None, **kw):
	try:
		fn(*a, **kw)
	except exc as e:
		if contains and contains.lower() not in str(e).lower():
			raise Fail(f"{fn.__name__} raised {exc.__name__} but message {str(e)!r} lacks {contains!r}")
		frappe.clear_messages()
		return e
	raise Fail(f"{fn.__name__} did not raise {exc.__name__}")


def offset(lat, lon, north_m):
	return lat + north_m / 111_320.0, lon


def run():
	results = []
	original_commit = frappe.db.commit

	def forbidden_commit(*a, **kw):
		raise RuntimeError("commit attempted during BB HR integration test")

	frappe.db.commit = forbidden_commit
	frappe.db.begin()
	try:
		ctx = _setup()
		for name, fn in TESTS:
			frappe.db.savepoint("bbhr_case")
			frappe.set_user("Administrator")
			try:
				fn(ctx)
				results.append((name, "PASS", ""))
			except Exception as e:
				frappe.db.rollback(save_point="bbhr_case")
				detail = str(e) if isinstance(e, Fail) else traceback.format_exc(limit=4)
				results.append((name, "FAIL", detail))
	finally:
		frappe.set_user("Administrator")
		frappe.db.rollback()
		frappe.db.commit = original_commit
		frappe.clear_document_cache("BB HR Settings", "BB HR Settings")
		frappe.clear_cache(doctype="BB HR Settings")

	# PDF rendering commits internally, so it runs after the rollback, with no test data present
	try:
		_pdf_check()
		results.append(("salary slip PDF (own slip)", "PASS", ""))
	except Exception as e:
		results.append(
			(
				"salary slip PDF (own slip)",
				"FAIL",
				str(e) if isinstance(e, Fail) else traceback.format_exc(limit=4),
			)
		)
	finally:
		frappe.set_user("Administrator")

	width = max(len(n) for n, _s, _d in results)
	for name, status, detail in results:
		print(f"{status}  {name.ljust(width)}  {detail.splitlines()[0] if detail else ''}")
		if status == "FAIL" and "\n" in detail:
			print("      " + detail.replace("\n", "\n      "))
	failed = sum(1 for _n, s, _d in results if s == "FAIL")
	print(f"\n{len(results) - failed} passed, {failed} failed (all changes rolled back)")
	if failed:
		raise SystemExit(1)


def _pdf_check():
	"""Read-only: render a real slip as its own (already linked) employee."""
	from bb_academy_hrms.api import salary

	slip, emp = frappe.db.get_value("Salary Slip", {"docstatus": 1}, ["name", "employee"])
	user = frappe.db.get_value("Employee", emp, "user_id")
	check(user, f"{emp} has no linked user; cannot test the employee PDF path")
	frappe.set_user(user)
	# outside a web request wkhtmltopdf would fetch assets from http://<site>:8000; use the public URL as a request would
	frappe.local.conf.host_name = f"https://{frappe.local.site}"
	frappe.local.conf.webserver_port = None  # in memory only; a real request uses its own host
	salary.download_salary_slip(slip)
	check(frappe.local.response.filecontent[:4] == b"%PDF", "download is not a PDF")
	check(frappe.local.response.type == "pdf", "wrong response type")


def _make_user(email, first_name, roles=()):
	if frappe.db.exists("User", email):
		frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": first_name,
			"send_welcome_email": 0,
			"user_type": "System User",
		}
	)
	user.flags.no_welcome_mail = True
	user.insert(ignore_permissions=True)
	for r in ("Employee", *roles):
		user.append("roles", {"role": r})
	user.save(ignore_permissions=True)
	frappe.clear_cache(user=email)
	return email


def _setup():
	settings = frappe.get_single("BB HR Settings")
	settings.enable_geofence = 1
	settings.default_radius = 150
	settings.accuracy_tolerance = 50
	settings.max_accuracy = 200
	settings.require_photo = 1
	settings.min_gap_seconds = 60
	settings.create_attendance = 1
	settings.set("office_locations", [])
	settings.append(
		"office_locations",
		{
			"location_name": "BBHR Test Office",
			"latitude": OFFICE[0],
			"longitude": OFFICE[1],
			"radius": 100,
			"enabled": 1,
		},
	)
	settings.save(ignore_permissions=True)
	frappe.clear_document_cache("BB HR Settings", "BB HR Settings")

	# employees: A has slips; B/C/D are other active employees
	slip_emp = frappe.db.get_value("Salary Slip", {"docstatus": 1}, "employee")
	check(slip_emp, "site needs at least one submitted salary slip")
	others = frappe.get_all(
		"Employee",
		filters={"status": "Active", "name": ["!=", slip_emp]},
		pluck="name",
		order_by="name",
		limit=3,
	)
	check(len(others) == 3, "site needs four active employees")
	a, b, c, mgr = slip_emp, others[0], others[1], others[2]

	users = {
		"a": _make_user("bbhr.a@test.invalid", "BBHR A"),
		"b": _make_user("bbhr.b@test.invalid", "BBHR B"),
		"mgr": _make_user("bbhr.mgr@test.invalid", "BBHR Manager"),
		"hr": _make_user("bbhr.hr@test.invalid", "BBHR HR", roles=("HR User",)),
		"nobody": _make_user("bbhr.nobody@test.invalid", "BBHR Unlinked"),
	}
	# clear any existing links to these employees, then link test users
	for emp, key in ((a, "a"), (b, "b"), (mgr, "mgr")):
		frappe.db.set_value("Employee", emp, "user_id", users[key], update_modified=False)
	# A reports to manager; B and C do not
	frappe.db.set_value("Employee", a, "reports_to", mgr, update_modified=False)
	for emp in (b, c):
		frappe.db.set_value("Employee", emp, "reports_to", None, update_modified=False)
	frappe.db.delete("Employee Checkin", {"employee": a, "time": [">=", f"{today()} 00:00:00"]})
	for att in frappe.get_all(
		"Attendance", {"employee": a, "attendance_date": today(), "docstatus": 1}, pluck="name"
	):
		frappe.get_doc("Attendance", att).cancel()
	frappe.db.delete("Attendance", {"employee": a, "attendance_date": today()})
	return frappe._dict(
		a=a,
		b=b,
		c=c,
		mgr=mgr,
		users=users,
		slip=frappe.db.get_value("Salary Slip", {"employee": a, "docstatus": 1}, "name"),
	)


def _punch(**kw):
	from bb_academy_hrms.api.attendance import punch

	inside = offset(*OFFICE, 20)
	args = dict(
		log_type="IN",
		latitude=inside[0],
		longitude=inside[1],
		accuracy=15,
		photo=PHOTO,
		request_id=frappe.generate_hash(length=20),
		device="test",
	)
	args.update(kw)
	return punch(**args)


def _count(emp):
	return frappe.db.count("Employee Checkin", {"employee": emp, "time": [">=", f"{today()} 00:00:00"]})


# ------------------------------------------------------------------------ cases
def t_geo_math(ctx):
	d = haversine_distance(*OFFICE, *offset(*OFFICE, 100))
	check(99 <= d <= 101, f"100 m north measured as {d}")
	from bb_academy_hrms.utils.geo import is_valid_coordinate, within_geofence

	check(
		not is_valid_coordinate(0, 0) and not is_valid_coordinate(91, 0) and not is_valid_coordinate("x", 1),
		"bad coords accepted",
	)
	check(within_geofence(140, 100, accuracy=500, tolerance=50), "tolerance should widen fence to 150")
	check(
		not within_geofence(160, 100, accuracy=500, tolerance=50),
		"accuracy beyond tolerance must not widen fence",
	)


def t_unlinked_user_denied(ctx):
	from bb_academy_hrms.api import dashboard, session

	frappe.set_user(ctx.users["nobody"])
	check(session.get_session()["employee"] is None, "unlinked user got an employee")
	raises(frappe.PermissionError, dashboard.get_dashboard, contains="not linked")
	raises(frappe.PermissionError, _punch, contains="not linked")


def t_outside_geofence_rejected(ctx):
	frappe.set_user(ctx.users["a"])
	before = _count(ctx.a)
	far = offset(*OFFICE, 400)
	raises(frappe.ValidationError, _punch, latitude=far[0], longitude=far[1], contains="Move within")
	check(_count(ctx.a) == before, "rejected punch left a check-in behind")


def t_weak_gps_rejected(ctx):
	frappe.set_user(ctx.users["a"])
	raises(frappe.ValidationError, _punch, accuracy=900, contains="accurate")
	raises(frappe.ValidationError, _punch, latitude=0, longitude=0, contains="location")


def t_photo_required_and_validated(ctx):
	frappe.set_user(ctx.users["a"])
	raises(frappe.ValidationError, _punch, photo=None, contains="photo")
	raises(
		frappe.ValidationError,
		_punch,
		photo="data:image/jpeg;base64," + base64.b64encode(b"<?php echo 1;").decode(),
		contains="JPEG",
	)
	raises(frappe.ValidationError, _punch, photo="not base64!!", contains="photo")
	raises(frappe.ValidationError, _punch, photo=CORRUPT, contains="could not be read")
	check(_count(ctx.a) == 0, "invalid photo punch created a check-in")


def t_full_day_flow(ctx):
	from bb_academy_hrms.api.attendance import get_status

	frappe.set_user(ctx.users["a"])
	rid = frappe.generate_hash(length=20)
	res = _punch(request_id=rid)
	check(res["ok"] and res["checkin"] and res["log_type"] == "IN", f"IN failed: {res}")
	check(
		res["location"] == "BBHR Test Office" and 15 <= res["distance"] <= 25, f"bad location/distance {res}"
	)
	ck = frappe.get_doc("Employee Checkin", res["checkin"])
	check(ck.employee == ctx.a and ck.bbhr_request_id == rid, "check-in not attributed correctly")
	file = frappe.get_doc("File", {"file_url": ck.bbhr_photo})
	check(file.is_private == 1 and file.attached_to_name == ck.name, "selfie is not a private attachment")
	att = frappe.get_doc("Attendance", res["attendance"])
	check(
		att.docstatus == 1 and att.status == "Present" and getdate(att.attendance_date) == getdate(today()),
		"attendance not created/submitted for payroll",
	)
	check(ck.attendance == att.name, "check-in not linked to attendance")

	# idempotent replay
	again = _punch(request_id=rid)
	check(
		again["replayed"] and again["checkin"] == res["checkin"], "replay did not return the original punch"
	)
	check(_count(ctx.a) == 1, "replay created a second check-in")

	# duplicate IN with a fresh request id
	raises(frappe.ValidationError, _punch, contains="already checked in")

	# OUT too soon, then allowed
	raises(frappe.ValidationError, _punch, log_type="OUT", contains="moments ago")
	frappe.db.set_single_value("BB HR Settings", "min_gap_seconds", 0)
	frappe.clear_document_cache("BB HR Settings", "BB HR Settings")
	time.sleep(1.1)
	out = _punch(log_type="OUT")
	check(out["ok"] and out["attendance"] == att.name, f"OUT failed: {out}")
	att.reload()
	check(
		att.out_time
		and str(att.out_time) == str(frappe.db.get_value("Employee Checkin", out["checkin"], "time")),
		"attendance out_time not updated",
	)
	raises(frappe.ValidationError, _punch, log_type="OUT", contains="not checked in")

	# split shift: second session the same day keeps one attendance record
	time.sleep(1.1)
	res2 = _punch()
	check(res2["attendance"] == att.name, "second session created another attendance")
	status = get_status()
	check(
		status["checked_in"] and len(status["logs"]) == 3 and status["next_action"] == "OUT",
		f"status wrong {status}",
	)
	frappe.db.set_single_value("BB HR Settings", "min_gap_seconds", 60)
	frappe.clear_document_cache("BB HR Settings", "BB HR Settings")


def t_request_id_not_reusable_by_others(ctx):
	frappe.set_user(ctx.users["a"])
	rid = frappe.generate_hash(length=20)
	frappe.db.set_single_value("BB HR Settings", "min_gap_seconds", 0)
	frappe.clear_document_cache("BB HR Settings", "BB HR Settings")
	frappe.db.delete("Employee Checkin", {"employee": ctx.a, "time": [">=", f"{today()} 00:00:00"]})
	_punch(request_id=rid)
	frappe.set_user(ctx.users["b"])
	raises(frappe.ValidationError, _punch, request_id=rid, contains="already used")
	raises(frappe.ValidationError, _punch, request_id="bad id!", contains="request id")


def t_unknown_punch_type(ctx):
	frappe.set_user(ctx.users["a"])
	raises(frappe.ValidationError, _punch, log_type="BREAK", contains="punch type")


def t_employee_isolation(ctx):
	from bb_academy_hrms.api import attendance, history, holidays, salary, team

	frappe.set_user(ctx.users["b"])
	raises(frappe.PermissionError, history.get_attendance_history, employee=ctx.a)
	raises(frappe.PermissionError, salary.get_salary_slips, employee=ctx.a)
	raises(frappe.PermissionError, salary.get_salary_slip, ctx.slip)
	raises(frappe.PermissionError, salary.download_salary_slip, ctx.slip)
	raises(frappe.PermissionError, holidays.get_holidays, employee=ctx.a)
	raises(frappe.PermissionError, team.get_team_overview)
	raises(frappe.PermissionError, team.get_directory)
	raises(frappe.PermissionError, team.get_exceptions)
	raises(frappe.PermissionError, team.get_hr_overview)
	own = history.get_attendance_history()
	check(own["employee"] == ctx.b, "own history resolved to someone else")
	ck = frappe.db.get_value("Employee Checkin", {"employee": ctx.a}, "name")
	if ck:
		raises(frappe.PermissionError, attendance.get_checkin_photo, ck)


def t_manager_scope(ctx):
	from bb_academy_hrms.api import history, salary, session, team

	frappe.set_user(ctx.users["mgr"])
	s = session.get_session()
	check(s["roles"]["is_manager"] and not s["roles"]["is_hr"], f"manager roles wrong {s['roles']}")
	overview = team.get_team_overview()
	ids = {r["employee"] for r in overview["rows"]}
	check(ctx.a in ids and ctx.b not in ids and ctx.mgr not in ids, f"team scope wrong: {ids}")
	check(
		history.get_attendance_history(employee=ctx.a)["employee"] == ctx.a,
		"manager cannot see report's attendance",
	)
	raises(frappe.PermissionError, history.get_attendance_history, employee=ctx.b)
	# salary is confidential even from the reporting manager
	raises(frappe.PermissionError, salary.get_salary_slips, employee=ctx.a)
	raises(frappe.PermissionError, salary.get_salary_slip, ctx.slip)
	raises(frappe.PermissionError, team.get_hr_overview)
	directory = team.get_directory()
	check({r.name for r in directory["rows"]} == {ctx.a}, "manager directory leaks other employees")
	check("cell_number" not in directory["rows"][0], "manager sees HR-only contact fields")
	ex = team.get_exceptions(from_date=add_days(today(), -6), to_date=today())
	check(all(r["employee"] == ctx.a for r in ex["rows"]), "exceptions leak employees outside the team")


def t_hr_scope(ctx):
	from bb_academy_hrms.api import salary, session, team

	frappe.set_user(ctx.users["hr"])
	check(session.get_session()["roles"]["is_hr"], "HR role not detected")
	rows = team.get_team_overview()["rows"]
	check(
		len(rows) == frappe.db.count("Employee", {"status": "Active"}),
		"HR does not see every active employee",
	)
	slips = salary.get_salary_slips(employee=ctx.a)
	check(slips["total"] >= 1, "HR cannot list salary slips")
	check(salary.get_salary_slip(ctx.slip)["employee"] == ctx.a, "HR cannot open a slip")
	ov = team.get_hr_overview()
	check(len(ov["trend"]) == 14 and "setup" in ov, "HR overview incomplete")


def t_own_salary(ctx):
	from bb_academy_hrms.api import salary

	frappe.set_user(ctx.users["a"])
	data = salary.get_salary_slips()
	check(data["employee"] == ctx.a and data["total"] >= 1, "employee cannot see own slips")
	detail = salary.get_salary_slip(ctx.slip)
	check(detail["net_pay"] > 0 and detail["earnings"], "slip detail empty")
	if detail["bank_account_no"]:
		check(detail["bank_account_no"].startswith("••••"), "bank account not masked")
	raises(frappe.DoesNotExistError, salary.get_salary_slip, "does-not-exist")


def t_holiday_lists_differ(ctx):
	from bb_academy_hrms.api import holidays

	lists = frappe.get_all("Holiday List", pluck="name", limit=2)
	if len(lists) < 2:
		return
	frappe.db.set_value("Employee", ctx.a, "holiday_list", lists[0], update_modified=False)
	frappe.db.set_value("Employee", ctx.b, "holiday_list", lists[1], update_modified=False)
	frappe.clear_document_cache("Employee", ctx.a)
	frappe.clear_document_cache("Employee", ctx.b)
	frappe.set_user(ctx.users["a"])
	ha = holidays.get_holidays()
	frappe.set_user(ctx.users["b"])
	hb = holidays.get_holidays()
	check(ha["holiday_list"] == lists[0] and hb["holiday_list"] == lists[1], "holiday list not per employee")
	check(
		[h["date"] for h in ha["holidays"]] != [h["date"] for h in hb["holidays"]],
		"different lists returned same days",
	)
	frappe.clear_document_cache("Employee", ctx.a)
	frappe.clear_document_cache("Employee", ctx.b)


def t_geofence_off_records_position(ctx):
	frappe.db.set_single_value(
		"BB HR Settings", {"enable_geofence": 0, "min_gap_seconds": 0, "require_photo": 0}
	)
	frappe.clear_document_cache("BB HR Settings", "BB HR Settings")
	frappe.set_user(ctx.users["b"])
	frappe.db.delete("Employee Checkin", {"employee": ctx.b, "time": [">=", f"{today()} 00:00:00"]})
	far = offset(*OFFICE, 5000)
	res = _punch(latitude=far[0], longitude=far[1], photo=None)
	check(res["ok"] and res["distance"] > 4900, "geofence-off punch should succeed and record distance")
	frappe.db.set_single_value(
		"BB HR Settings", {"enable_geofence": 1, "min_gap_seconds": 60, "require_photo": 1}
	)
	frappe.clear_document_cache("BB HR Settings", "BB HR Settings")


TESTS = [
	("geo math", t_geo_math),
	("unlinked user denied", t_unlinked_user_denied),
	("outside geofence rejected", t_outside_geofence_rejected),
	("weak / missing GPS rejected", t_weak_gps_rejected),
	("photo required and validated", t_photo_required_and_validated),
	("full day: IN, replay, dup, OUT, split", t_full_day_flow),
	("request id bound to employee", t_request_id_not_reusable_by_others),
	("unknown punch type", t_unknown_punch_type),
	("employee data isolation", t_employee_isolation),
	("manager scope (no salary)", t_manager_scope),
	("HR scope", t_hr_scope),
	("own salary + PDF", t_own_salary),
	("holiday lists per employee", t_holiday_lists_differ),
	("geofence off still records", t_geofence_off_records_position),
]
