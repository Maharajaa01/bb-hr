"""ZKTeco push (ADMS / "iclock") receiver.

ZKTeco terminals such as the MB400 can push punches over HTTP to a server set under
Comm > Cloud Server Setting. The device talks a small plain-text protocol:

  GET  /iclock/cdata?SN=..&options=all   handshake; we answer with upload options
  POST /iclock/cdata?SN=..&table=ATTLOG  punches, one per line:
                                         PIN \t YYYY-MM-DD HH:MM:SS \t status \t verify \t ...
  GET  /iclock/getrequest?SN=..          polls for commands: queued BB HR Device Commands
                                         as "C:<id>:<command>" lines, or "OK" when none
  POST /iclock/devicecmd?SN=..           command results: ID=<id>&Return=<code>&CMD=..

Each punch becomes an Employee Checkin for the Employee whose Attendance Device ID is
the device user ID, and the day's Attendance is kept in step the same way as a punch
from the BB HR app.

The device marks rows as sent only when it gets "OK", so anything we answer with an
error is retried later. Re-sent rows are harmless: a punch that already exists for the
employee at that second is skipped.
"""

import re
from datetime import timedelta
from zoneinfo import ZoneInfo

import frappe
from frappe.utils import cint, get_datetime, get_system_timezone, getdate, now_datetime, time_diff_in_seconds
from werkzeug.wrappers import Response

DOCTYPE = "BB HR Biometric Device"
SN_RE = re.compile(r"^[A-Za-z0-9_-]{4,40}$")
PIN_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
MAX_AUTO_REGISTERED = 10  # unknown serials registered (disabled) before we stop recording new ones
FUTURE_TOLERANCE = timedelta(minutes=10)
MAX_UNMATCHED = 50

# ZKTeco punch states (the key pressed on the keypad)
IN_STATES = {0, 3, 4}  # check-in, break-in, overtime-in
OUT_STATES = {1, 2, 5}  # check-out, break-out, overtime-out

ENDPOINTS = {"cdata", "getrequest", "devicecmd", "ping", "registry", "push", "querydata"}


class ZKPushRenderer:
	"""Frappe page renderer for /iclock/* (registered via the `page_renderer` hook)."""

	def __init__(self, path=None, http_status_code=None):
		self.path = (path or frappe.local.request.path or "").strip("/ ")

	def can_render(self):
		parts = self.path.split("/")
		return len(parts) == 2 and parts[0] == "iclock"

	def render(self):
		endpoint = self.path.split("/")[1].removesuffix(".aspx")
		try:
			status, body = handle(endpoint)
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title="BB HR: biometric push failed")
			# not "OK": the device keeps the rows and retries after ErrorDelay
			status, body = 500, "ERROR"
		response = Response(body, status=status, mimetype="text/plain")
		response.headers["Cache-Control"] = "no-store"
		return response


# ------------------------------------------------------------------- dispatch
def handle(endpoint):
	request = frappe.local.request
	if endpoint != "getrequest":  # the 10-second poll would drown everything else
		_log().info(
			"%s %s %s body=%r",
			request.method,
			request.path,
			request.query_string.decode(errors="replace")[:500],
			_body()[:2000] if request.method == "POST" else "",
		)
	sn = (request.args.get("SN") or "").strip()
	if not SN_RE.match(sn):
		return 400, "Missing or invalid SN"

	device = _get_device(sn)
	if not device:
		return 403, "Device not registered"

	ip = frappe.local.request_ip
	if device.allowed_ip and device.allowed_ip.strip() != ip:
		return 403, "IP not allowed"

	seen = {"last_seen": now_datetime(), "last_ip": ip}
	if request.args.get("pushver"):
		seen["firmware"] = request.args.get("pushver")[:140]
	frappe.db.set_value(DOCTYPE, device.name, seen, update_modified=False)
	frappe.local.flags.commit = True  # Frappe rolls back GET requests otherwise

	if not device.enabled:
		return 403, "Device disabled"

	if endpoint == "cdata" and request.method == "GET":
		return 200, _handshake(device)

	if endpoint == "cdata" and request.method == "POST":
		table = (request.args.get("table") or "").upper()
		if table == "ATTLOG":
			count = ingest_attlog(device, _body(), request.args.get("Stamp"))
			return 200, f"OK: {count}"
		# OPERLOG, ATTPHOTO, user/fingerprint data: not used, acknowledge so it isn't resent
		return 200, "OK"

	if endpoint == "getrequest":
		return 200, next_commands(device) or "OK"

	if endpoint == "devicecmd" and request.method == "POST":
		record_command_results(device, _body())
		return 200, "OK"

	if endpoint not in ENDPOINTS:
		return 404, "Unknown endpoint"
	# ping, registry, ...
	return 200, "OK"


def _log():
	# logs/bbhr_biometric.log in the bench: every upload except the command poll
	return frappe.logger("bbhr_biometric", file_count=5, max_size=5_000_000)


def _get_device(sn):
	device = frappe.db.get_value(
		DOCTYPE,
		sn,
		["name", "serial_number", "device_name", "enabled", "office_location", "punch_direction",
		 "import_from", "allowed_ip", "last_stamp", "unmatched_user_ids"],
		as_dict=True,
	)
	if device:
		return device

	# first contact: register it disabled so HR only has to tick "Enabled"
	if frappe.db.count(DOCTYPE, {"enabled": 0}) >= MAX_AUTO_REGISTERED:
		return None
	doc = frappe.get_doc({"doctype": DOCTYPE, "serial_number": sn, "enabled": 0})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return _get_device(sn)


def _body():
	request = frappe.local.request
	data = request.get_data(as_text=True)
	if data:
		return data
	# sent as a form: each line ended up as a key without a value
	return "\n".join(k + (f"={v}" if v else "") for k, v in request.form.items(multi=True))


def _handshake(device):
	stamp = device.last_stamp or "None"
	return "\n".join(
		[
			f"GET OPTION FROM: {device.serial_number}",
			f"ATTLOGStamp={stamp}",
			"OPERLOGStamp=9999",
			"ATTPHOTOStamp=None",
			"ErrorDelay=30",
			"Delay=10",
			"TransTimes=00:00;14:05",
			"TransInterval=1",
			"TransFlag=TransData AttLog",
			f"TimeZone={_tz_value()}",
			"Realtime=1",
			"Encrypt=None",
		]
	)


def _tz_value():
	"""The handshake's TimeZone value: whole hours, or minutes for a fractional offset.

	ADMS firmware parses TimeZone as an integer and treats |value| <= 12 as hours and
	anything larger as minutes. "5.5" is truncated to 5 and drags an IST device's clock
	back to UTC+5:00 on every handshake, so IST must go out as 330.
	"""
	offset = now_datetime().replace(tzinfo=ZoneInfo(get_system_timezone())).utcoffset()
	minutes = int(offset.total_seconds() // 60)
	return minutes // 60 if minutes % 60 == 0 else minutes


# -------------------------------------------------------------------- punches
def parse_attlog(body):
	"""[(pin, datetime, state)] from an ATTLOG upload; malformed lines are dropped."""
	rows = []
	for line in (body or "").splitlines():
		parts = line.strip().split("\t")
		if len(parts) < 2:
			continue
		pin = parts[0].strip()
		if not PIN_RE.match(pin):
			continue
		try:
			at = get_datetime(parts[1].strip()).replace(microsecond=0)
		except Exception:
			continue
		state = cint(parts[2]) if len(parts) > 2 and parts[2].strip().isdigit() else 255
		rows.append((pin, at, state))
	rows.sort(key=lambda r: r[1])
	return rows


def ingest_attlog(device, body, stamp=None):
	"""Import an ATTLOG upload. Returns the number of lines acknowledged."""
	rows = parse_attlog(body)
	frappe.set_user("Administrator")  # device requests are Guest; documents are owned by Administrator
	try:
		imported, last_punch, errors, too_old = 0, None, [], []
		unmatched = set(filter(None, (device.unmatched_user_ids or "").split()))
		employees = {}
		for pin, at, state in rows:
			if pin not in employees:
				employees[pin] = _employee_for(pin)
			emp = employees[pin]
			if not emp:
				unmatched.add(pin)
				continue
			unmatched.discard(pin)
			result = _import_punch(device, emp, at, state)
			if result == "too_old":
				too_old.append(at)
			elif result is True:
				imported += 1
				last_punch = max(last_punch or at, at)
			elif result:
				errors.append(f"{pin} {at}: {result}")

		values = {"unmatched_user_ids": "\n".join(sorted(unmatched)[:MAX_UNMATCHED]) or None}
		if stamp and stamp.strip().isdigit():
			values["last_stamp"] = stamp.strip()
		if imported:
			values["punches_received"] = cint(frappe.db.get_value(DOCTYPE, device.name, "punches_received")) + imported
			values["last_punch"] = last_punch
		if too_old:
			errors.append(
				f"{len(too_old)} punch(es) skipped as older than Import Punches From "
				f"(device time {max(too_old)}); check the device clock"
			)
		if errors:
			values["last_error"] = f"{now_datetime():%Y-%m-%d %H:%M} " + "\n".join(errors[-5:])
		frappe.db.set_value(DOCTYPE, device.name, values, update_modified=False)
		frappe.db.commit()
		return len(rows)
	finally:
		frappe.set_user("Guest")


def _employee_for(pin):
	found = frappe.get_all(
		"Employee",
		filters={"attendance_device_id": pin, "status": "Active"},
		fields=["name", "employee_name", "company", "department"],
		limit=2,
	)
	return frappe._dict(found[0]) if len(found) == 1 else None


def _import_punch(device, emp, at, state):
	"""True when imported, None when skipped on purpose ("too_old" before Import Punches From),
	an error message when refused."""
	from bb_academy_hrms.api.attendance import _sync_attendance, day_logs
	from bb_academy_hrms.utils.settings import get_settings

	if device.import_from and at < get_datetime(device.import_from):
		return "too_old"
	if at > now_datetime() + FUTURE_TOLERANCE:
		return "punch time is in the future; check the device clock"

	# same lock as an app punch, so the two never race for one employee
	frappe.db.sql("select name from `tabEmployee` where name=%s for update", emp.name)

	if frappe.db.exists("Employee Checkin", {"employee": emp.name, "time": at}):
		return None  # re-sent row

	settings = get_settings()
	date = getdate(at)
	logs = day_logs(emp.name, date)

	# a second scan right after the first (or right after an app punch) is the same punch
	gap = max(settings.min_gap_seconds, 1)
	if any(abs(time_diff_in_seconds(at, l.time)) < gap for l in logs):
		return None

	before = [l for l in logs if get_datetime(l.time) <= at]
	previous = before[-1] if before else None
	log_type = "OUT" if previous and previous.log_type == "IN" else "IN"
	if device.punch_direction == "Device punch key":
		if state in IN_STATES:
			log_type = "IN"
		elif state in OUT_STATES:
			log_type = "OUT"

	frappe.db.savepoint("bbhr_biometric")
	try:
		doc = frappe.new_doc("Employee Checkin")
		doc.employee = emp.name
		doc.log_type = log_type
		doc.time = at
		doc.device_id = f"{device.device_name or device.serial_number} ({device.serial_number})"[:140]
		doc.bbhr_office_location = device.office_location
		doc.flags.ignore_permissions = True
		doc.insert()
	except frappe.ValidationError as e:
		frappe.db.rollback(save_point="bbhr_biometric")
		frappe.clear_messages()
		return frappe.utils.strip_html(str(e))[:200] or type(e).__name__

	if settings.create_attendance:
		_attendance, warning = _sync_attendance(emp, date, day_logs(emp.name, date), doc.name)
		if warning:
			frappe.clear_messages()
	return True


# ------------------------------------------------------------------- commands
# The server cannot call the device; it queues commands (BB HR Device Command) and the
# device collects them on its getrequest poll as "C:<id>:<command>" lines, then reports
# each result on devicecmd as "ID=<id>&Return=<code>&CMD=<name>" (Return=0 is success).
COMMAND_DOCTYPE = "BB HR Device Command"
COMMANDS_PER_POLL = 20
RESEND_AFTER = timedelta(minutes=5)  # a sent command with no reply is sent again
MAX_ATTEMPTS = 3
DEVICE_NAME_LEN = 24  # longest user name the terminals store


def next_commands(device):
	"""The getrequest reply: pending commands (and unanswered ones due a resend)."""
	now = now_datetime()
	stale = now - RESEND_AFTER

	# gave up waiting for a reply
	frappe.db.sql(
		f"""update `tab{COMMAND_DOCTYPE}` set status='Failed', return_code='no reply'
		where device=%s and status='Sent' and attempts>=%s and sent_at<%s""",
		(device.name, MAX_ATTEMPTS, stale),
	)
	rows = frappe.db.sql(
		f"""select name, command from `tab{COMMAND_DOCTYPE}`
		where device=%s and (status='Pending' or (status='Sent' and sent_at<%s))
		order by name limit %s""",
		(device.name, stale, COMMANDS_PER_POLL),
		as_dict=True,
	)
	if not rows:
		return None
	frappe.db.sql(
		f"""update `tab{COMMAND_DOCTYPE}` set status='Sent', sent_at=%s, attempts=attempts+1
		where name in %s""",
		(now, tuple(r.name for r in rows)),
	)
	_log().info("%s: sent commands %s", device.name, ",".join(str(r.name) for r in rows))
	return "\n".join(f"C:{r.name}:{r.command}" for r in rows) + "\n"


def parse_command_results(body):
	"""{command id: return code} from a devicecmd upload. Records may be separated by
	newlines or '&' (or arrive as form fields), so a new record starts at every ID=."""
	results, current = {}, None
	for token in re.split(r"[&\r\n]+", body or ""):
		key, _, value = token.partition("=")
		key, value = key.strip(), value.strip()
		if key == "ID":
			current = cint(value) if value.isdigit() else None
		elif key == "Return" and current:
			results[current] = value
	return results


def record_command_results(device, body):
	now = now_datetime()
	for name, code in parse_command_results(body).items():
		frappe.db.sql(
			f"""update `tab{COMMAND_DOCTYPE}` set status=%s, return_code=%s, done_at=%s
			where name=%s and device=%s""",
			("Done" if code == "0" else "Failed", code[:140], now, name, device.name),
		)


def _device_text(value, limit=None):
	"""A field value safe inside a tab-separated command line."""
	value = re.sub(r"\s+", " ", str(value or "")).strip()
	return value[:limit] if limit else value


def user_command(pin, name):
	# Only PIN and Name: existing users keep their privilege (device admin), password and card.
	return f"DATA UPDATE USERINFO PIN={pin}\tName={_device_text(name, DEVICE_NAME_LEN)}"


# ------------------------------------------------------------- employee sync
def _taken_device_ids():
	return {
		str(v).strip()
		for v in frappe.get_all("Employee", filters={"attendance_device_id": ["is", "set"]}, pluck="attendance_device_id")
	}


def _pin_from_employee_id(employee, taken):
	"""HR-EMP-00007 -> "7" when that number is free, else None."""
	digits = re.findall(r"\d+", employee or "")
	pin = str(int(digits[-1])) if digits and 0 < int(digits[-1]) < 10**9 else None
	return pin if pin and pin not in taken else None


def _next_free_pin(taken):
	n = max((int(v) for v in taken if v.isdigit()), default=0) + 1
	while str(n) in taken:
		n += 1
	return str(n)


def fill_missing_device_ids():
	"""Give every active employee without an Attendance Device ID a numeric one.

	The number comes from the employee ID (HR-EMP-00007 -> 7) so staff can work it out;
	when that number is taken, the next free number is used. Returns [(employee, name, id)].
	"""
	taken = _taken_device_ids()
	missing = frappe.get_all(
		"Employee",
		filters={"status": "Active", "attendance_device_id": ["is", "not set"]},
		fields=["name", "employee_name"],
		order_by="name asc",
	)
	# first pass: everyone whose employee number is free keeps it, so one clash
	# doesn't shift every later employee
	pins = {}
	for emp in missing:
		pin = _pin_from_employee_id(emp.name, taken)
		if pin:
			pins[emp.name] = pin
			taken.add(pin)
	# second pass: the rest get numbers after the highest one in use
	assigned = []
	for emp in missing:
		pin = pins.get(emp.name)
		if not pin:
			pin = _next_free_pin(taken)
			taken.add(pin)
		frappe.db.set_value("Employee", emp.name, "attendance_device_id", pin)
		assigned.append((emp.name, emp.employee_name, pin))
	return assigned


def queue_employee_users(device_name):
	"""Queue a create/update of every active employee with a device ID as a user on the
	device. Returns (queued, skipped) where skipped lists employees with an unusable ID."""
	employees = frappe.get_all(
		"Employee",
		filters={"status": "Active", "attendance_device_id": ["is", "set"]},
		fields=["name", "employee_name", "attendance_device_id"],
		order_by="name asc",
	)
	# re-clicking replaces what is still waiting instead of piling up duplicates
	frappe.db.delete(COMMAND_DOCTYPE, {"device": device_name, "status": "Pending", "command": ["like", "DATA UPDATE USERINFO %"]})

	queued, skipped = 0, []
	for emp in employees:
		pin = str(emp.attendance_device_id).strip()
		if not PIN_RE.match(pin):
			skipped.append(f"{emp.name} ({emp.employee_name}): device ID {pin!r}")
			continue
		frappe.get_doc(
			{
				"doctype": COMMAND_DOCTYPE,
				"device": device_name,
				"employee": emp.name,
				"status": "Pending",
				"command": user_command(pin, emp.employee_name or emp.name),
			}
		).insert(ignore_permissions=True)
		queued += 1
	return queued, skipped


# ------------------------------------------------- automatic employee -> device sync
# Employees reach the terminals without anyone clicking "Send Employees to Device":
#   * Employee validate: an active employee without an Attendance Device ID gets one.
#   * Employee on_update: a new, renamed, re-numbered or re-activated employee is queued
#     for every enabled device.
#   * hourly sync_employees_to_devices: re-queues whatever a device does not have yet
#     (a failed send, a device added later, an employee written straight to the DB).
# A device that is offline simply does not poll; its commands stay Pending and are
# collected on its first getrequest once it is back online.
MAX_FAILED_RETRIES = 5  # a command the device keeps rejecting is not re-queued forever


def employee_validate(doc, method=None):
	if doc.status != "Active" or (doc.attendance_device_id or "").strip():
		return
	taken = _taken_device_ids()
	doc.attendance_device_id = _pin_from_employee_id(doc.name, taken) or _next_free_pin(taken)


def employee_on_update(doc, method=None):
	if doc.status != "Active":
		return
	pin = str(doc.attendance_device_id or "").strip()
	if not PIN_RE.match(pin):
		return
	if not any(doc.has_value_changed(f) for f in ("attendance_device_id", "employee_name", "status")):
		return
	try:
		for device in frappe.get_all(DOCTYPE, filters={"enabled": 1}, pluck="name"):
			queue_user(device, doc.name, pin, doc.employee_name or doc.name)
	except Exception:
		# never block saving an Employee; the hourly sync picks it up
		frappe.log_error(title="BB HR: could not queue employee for biometric device")


def queue_user(device, employee, pin, name, replace_pending=True):
	"""Queue a create/update of one employee on one device. Returns True when queued."""
	command = user_command(pin, name)
	if replace_pending:
		# an older pending update for this employee (e.g. previous name) is superseded
		frappe.db.delete(
			COMMAND_DOCTYPE,
			{"device": device, "employee": employee, "status": "Pending", "command": ["like", "DATA UPDATE USERINFO %"]},
		)
	frappe.get_doc(
		{"doctype": COMMAND_DOCTYPE, "device": device, "employee": employee, "status": "Pending", "command": command}
	).insert(ignore_permissions=True)
	return True


def sync_employees_to_devices():
	"""Scheduler (hourly): make sure every enabled device has every active employee.

	Fills missing Attendance Device IDs, then queues a user update wherever the device
	has neither received the current PIN+name (Done) nor has it waiting (Pending/Sent).
	Returns {device: number queued}.
	"""
	devices = frappe.get_all(DOCTYPE, filters={"enabled": 1}, pluck="name")
	if not devices:
		return {}
	fill_missing_device_ids()
	employees = frappe.get_all(
		"Employee",
		filters={"status": "Active", "attendance_device_id": ["is", "set"]},
		fields=["name", "employee_name", "attendance_device_id"],
		order_by="name asc",
	)
	result = {}
	for device in devices:
		rows = frappe.get_all(
			COMMAND_DOCTYPE,
			filters={"device": device, "command": ["like", "DATA UPDATE USERINFO %"]},
			fields=["command", "status"],
		)
		ok = {r.command for r in rows if r.status in ("Pending", "Sent", "Done")}
		failed = {}
		for r in rows:
			if r.status == "Failed":
				failed[r.command] = failed.get(r.command, 0) + 1
		queued = 0
		for emp in employees:
			pin = str(emp.attendance_device_id).strip()
			if not PIN_RE.match(pin):
				continue
			command = user_command(pin, emp.employee_name or emp.name)
			if command in ok or failed.get(command, 0) >= MAX_FAILED_RETRIES:
				continue
			queue_user(device, emp.name, pin, emp.employee_name or emp.name)
			queued += 1
		if queued:
			_log().info("%s: sync queued %s employee(s)", device, queued)
		result[device] = queued
	frappe.db.commit()
	return result
