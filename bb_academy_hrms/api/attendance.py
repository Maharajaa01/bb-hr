"""Geo-fenced check-in / check-out.

The client never decides anything that matters here: the punch time is the
server clock, the geofence is recomputed from the submitted fix, and success
is only reported once the Employee Checkin row exists. The client-side
distance preview is a courtesy, not a check.

Duplicate protection, in order:
  1. a row lock on the Employee serialises concurrent punches,
  2. `request_id` (unique column) makes a retried request return the original punch,
  3. the IN/OUT sequence must alternate within the day,
  4. punches closer together than `min_gap_seconds` are refused.
"""

import base64
import binascii
import re

import frappe
from frappe import _
from frappe.utils import (
	cint,
	flt,
	get_datetime,
	getdate,
	now_datetime,
	time_diff_in_seconds,
)

from bb_academy_hrms.utils import permissions as perm
from bb_academy_hrms.utils.geo import is_valid_coordinate, nearest_location, within_geofence
from bb_academy_hrms.utils.settings import get_settings

MAX_PHOTO_BYTES = 2 * 1024 * 1024
IMAGE_SIGNATURES = {
	b"\xff\xd8\xff": "jpg",
	b"\x89PNG\r\n\x1a\n": "png",
	b"RIFF": "webp",  # RIFF....WEBP, checked below
}
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


# --------------------------------------------------------------------- helpers
def day_logs(employee, date):
	return frappe.get_all(
		"Employee Checkin",
		filters={"employee": employee, "time": ["between", [f"{date} 00:00:00", f"{date} 23:59:59.999999"]]},
		fields=["name", "log_type", "time", "bbhr_office_location", "bbhr_distance", "attendance", "shift"],
		order_by="time asc, creation asc",
		ignore_permissions=True,
	)


def worked_seconds(logs, until=None):
	"""Sum of IN->OUT pairs. An open IN counts up to `until` when given."""
	total, open_since = 0, None
	for log in logs:
		if log.log_type == "IN":
			open_since = open_since or log.time
		elif log.log_type == "OUT" and open_since:
			total += time_diff_in_seconds(log.time, open_since)
			open_since = None
	if open_since and until:
		total += max(0, time_diff_in_seconds(until, open_since))
	return total


def shift_info(employee, at=None):
	"""The employee's shift for `at`, with late-entry grace. {} when none is assigned."""
	from hrms.hr.doctype.shift_assignment.shift_assignment import get_employee_shift

	at = at or now_datetime()
	try:
		details = get_employee_shift(employee, get_datetime(at), consider_default_shift=True)
	except Exception:
		frappe.log_error(title="BB HR: shift lookup failed")
		details = None
	if not details or not details.get("shift_type"):
		return {}
	st = details.shift_type
	grace = cint(st.late_entry_grace_period) if st.get("enable_late_entry_marking") else 0
	return {
		"name": st.name,
		"start": str(details.start_datetime),
		"end": str(details.end_datetime),
		"grace_minutes": grace,
	}


def late_minutes(first_in, shift):
	if not first_in or not shift or not shift.get("start"):
		return 0
	start = get_datetime(shift["start"])
	if getdate(start) != getdate(first_in):
		return 0
	delta = time_diff_in_seconds(first_in, start) / 60 - cint(shift.get("grace_minutes"))
	return max(0, int(delta))


def _decode_photo(photo):
	"""Accept a data URL or bare base64 image; return (bytes, extension). Throws on anything else."""
	if not photo or not isinstance(photo, str):
		frappe.throw(
			_("A photo is required to check in. Allow camera access and take a selfie."),
			title=_("Photo Required"),
		)
	if photo.startswith("data:"):
		header, _sep, photo = photo.partition(",")
		if ";base64" not in header:
			frappe.throw(_("The photo could not be read. Please retake it."), title=_("Invalid Photo"))
	if len(photo) > MAX_PHOTO_BYTES * 4 // 3 + 4:
		frappe.throw(_("The photo is too large. Please retake it."), title=_("Invalid Photo"))
	try:
		content = base64.b64decode(photo, validate=True)
	except (binascii.Error, ValueError):
		frappe.throw(_("The photo could not be read. Please retake it."), title=_("Invalid Photo"))
	if not content or len(content) > MAX_PHOTO_BYTES:
		frappe.throw(_("The photo is empty or too large. Please retake it."), title=_("Invalid Photo"))
	ext = next(
		(
			e
			for sig, e in IMAGE_SIGNATURES.items()
			if content.startswith(sig) and (e != "webp" or content[8:12] == b"WEBP")
		),
		None,
	)
	if not ext:
		frappe.throw(_("The photo must be a JPEG, PNG or WebP image."), title=_("Invalid Photo"))
	# a valid header is not a valid image; decode it so a corrupt upload is a clean rejection, not a 500
	from io import BytesIO

	from PIL import Image

	try:
		with Image.open(BytesIO(content)) as img:
			img.verify()
	except Exception:
		frappe.throw(_("The photo could not be read. Please retake it."), title=_("Invalid Photo"))
	return content, ext


def _check_location(settings, latitude, longitude, accuracy):
	"""Returns (location_name, distance). Throws when the geofence refuses the fix."""
	has_fix = is_valid_coordinate(latitude, longitude)
	if not settings.enable_geofence:
		if not has_fix:
			return None, None
		loc, distance, _radius = nearest_location(
			latitude, longitude, settings.office_locations, settings.default_radius
		)
		return (loc.location_name if loc else None), distance

	if not settings.office_locations:
		frappe.throw(
			_("No office location is configured for check-in yet. Ask HR to add one in BB HR Settings."),
			title=_("No Office Location"),
		)
	if not has_fix:
		frappe.throw(
			_("We could not read your location. Turn on GPS, allow location access, and try again."),
			title=_("Location Required"),
		)
	accuracy = flt(accuracy)
	if accuracy <= 0 or accuracy > settings.max_accuracy:
		frappe.throw(
			_(
				"Your location is only accurate to about {0} m (we need {1} m or better). Move near a window or outdoors and try again."
			).format(int(accuracy) if accuracy > 0 else "?", settings.max_accuracy),
			title=_("Weak GPS Signal"),
		)
	loc, distance, radius = nearest_location(
		latitude, longitude, settings.office_locations, settings.default_radius
	)
	if not within_geofence(distance, radius, accuracy, settings.accuracy_tolerance):
		frappe.throw(
			_("You are about {0} m from {1}. Move within {2} m of the office and try again.").format(
				int(distance), loc.location_name, radius
			),
			title=_("Outside Office Area"),
		)
	return loc.location_name, distance


def _sync_attendance(emp, date, logs, checkin_name):
	"""Create (first IN) or update (OUT) the day's Attendance. Returns (attendance_name, warning)."""
	existing = frappe.db.get_value(
		"Attendance",
		{"employee": emp.name, "attendance_date": date, "docstatus": ["<", 2]},
		["name", "docstatus", "status"],
		as_dict=True,
	)
	ins = [l.time for l in logs if l.log_type == "IN"]
	outs = [l.time for l in logs if l.log_type == "OUT"]
	hours = round(worked_seconds(logs) / 3600, 2)

	if existing:
		values = {"working_hours": hours}
		if ins:
			values["in_time"] = ins[0]
		if outs and logs[-1].log_type == "OUT":
			values["out_time"] = outs[-1]
		frappe.db.set_value("Attendance", existing.name, values, update_modified=False)
		name = existing.name
	else:
		frappe.db.savepoint("bbhr_attendance")
		previous_mute = frappe.flags.mute_messages
		frappe.flags.mute_messages = True
		try:
			att = frappe.new_doc("Attendance")
			att.employee = emp.name
			att.employee_name = emp.employee_name
			att.attendance_date = date
			att.company = emp.company
			att.department = emp.department
			att.status = "Present"
			att.in_time = ins[0] if ins else None
			att.shift = logs[0].shift if logs else None
			att.working_hours = hours
			att.flags.ignore_permissions = True
			att.insert()
			att.submit()
			name = att.name
		except Exception as e:
			frappe.db.rollback(save_point="bbhr_attendance")
			frappe.log_error(title="BB HR: could not create Attendance")
			return None, _(
				"Your punch is saved, but the attendance record could not be created ({0}). HR has been notified."
			).format(frappe.utils.strip_html(str(e))[:140])
		finally:
			frappe.flags.mute_messages = previous_mute

	frappe.db.set_value("Employee Checkin", checkin_name, "attendance", name, update_modified=False)
	return name, None


def _serialize_log(log):
	return {
		"name": log.name,
		"log_type": log.log_type,
		"time": str(log.time),
		"location": log.get("bbhr_office_location"),
		"distance": log.get("bbhr_distance"),
	}


# ------------------------------------------------------------------- endpoints
@frappe.whitelist(methods=["GET"])
def get_status():
	"""Everything the check-in screen needs to draw itself."""
	emp = perm.require_employee()
	now = now_datetime()
	date = getdate(now)
	logs = day_logs(emp.name, date)
	settings = get_settings()
	shift = shift_info(emp.name, now)
	last = logs[-1] if logs else None
	attendance = frappe.db.get_value(
		"Attendance",
		{"employee": emp.name, "attendance_date": date, "docstatus": ["<", 2]},
		["name", "status", "working_hours", "in_time", "out_time", "leave_type"],
		as_dict=True,
	)
	from bb_academy_hrms.api.holidays import holiday_on

	return {
		"employee": emp.name,
		"employee_name": emp.employee_name,
		"date": str(date),
		"server_time": str(now),
		"logs": [_serialize_log(l) for l in logs],
		"checked_in": bool(last and last.log_type == "IN"),
		"next_action": "OUT" if last and last.log_type == "IN" else "IN",
		"first_in": str(logs[0].time) if logs and logs[0].log_type == "IN" else None,
		"last_out": str(last.time) if last and last.log_type == "OUT" else None,
		"worked_hours": round(worked_seconds(logs, until=now) / 3600, 2),
		"late_minutes": late_minutes(logs[0].time if logs else None, shift),
		"shift": shift,
		"holiday": holiday_on(emp.name, date),
		"attendance": attendance,
		"rules": {
			"geofence": bool(settings.enable_geofence),
			"require_photo": bool(settings.require_photo),
			"max_accuracy": settings.max_accuracy,
			"accuracy_tolerance": settings.accuracy_tolerance,
			"min_gap_seconds": settings.min_gap_seconds,
			"locations": [
				{
					"name": l.location_name,
					"latitude": l.latitude,
					"longitude": l.longitude,
					"radius": l.radius,
				}
				for l in settings.office_locations
			],
		},
	}


@frappe.whitelist(methods=["POST"])
def punch(log_type, latitude=None, longitude=None, accuracy=None, photo=None, request_id=None, device=None):
	"""Record one check-in (IN) or check-out (OUT) for the logged-in employee."""
	log_type = (log_type or "").upper()
	if log_type not in ("IN", "OUT"):
		frappe.throw(_("Unknown punch type."), frappe.ValidationError)
	if request_id and not REQUEST_ID_RE.match(str(request_id)):
		frappe.throw(_("Invalid request id."), frappe.ValidationError)

	emp = perm.require_employee()

	# 1. serialise punches for this employee
	frappe.db.sql("select name from `tabEmployee` where name=%s for update", emp.name)

	# 2. a retried request returns the punch it already made
	if request_id:
		previous = frappe.db.get_value(
			"Employee Checkin",
			{"bbhr_request_id": request_id},
			["name", "employee", "log_type", "time", "bbhr_office_location", "bbhr_distance", "attendance"],
			as_dict=True,
		)
		if previous:
			if previous.employee != emp.name or previous.log_type != log_type:
				frappe.throw(_("This request was already used."), frappe.ValidationError)
			return _result(previous, previous.attendance, None, replayed=True)

	settings = get_settings()
	now = now_datetime()
	date = getdate(now)
	logs = day_logs(emp.name, date)
	last = logs[-1] if logs else None

	# 3. sequence
	if log_type == "IN" and last and last.log_type == "IN":
		frappe.throw(
			_("You are already checked in since {0}. Check out first.").format(
				get_datetime(last.time).strftime("%I:%M %p")
			),
			title=_("Already Checked In"),
		)
	if log_type == "OUT" and not (last and last.log_type == "IN"):
		frappe.throw(
			_("You have not checked in yet, so there is nothing to check out of."), title=_("Not Checked In")
		)

	# 4. minimum gap (never below one second: HRMS refuses two logs with the same timestamp)
	if last and time_diff_in_seconds(now, last.time) < max(settings.min_gap_seconds, 1):
		frappe.throw(
			_("Your last punch was moments ago. Wait a minute before punching again."),
			title=_("Too Soon"),
		)

	location_name, distance = _check_location(settings, latitude, longitude, accuracy)
	content, ext = _decode_photo(photo) if (settings.require_photo or photo) else (None, None)

	doc = frappe.new_doc("Employee Checkin")
	doc.employee = emp.name
	doc.log_type = log_type
	doc.time = now
	doc.device_id = ("BB HR · " + (device or "web"))[:140]
	doc.bbhr_request_id = request_id or None
	doc.bbhr_office_location = location_name
	doc.bbhr_distance = distance
	doc.bbhr_accuracy = flt(accuracy) or None
	if is_valid_coordinate(latitude, longitude):
		doc.latitude = flt(latitude)
		doc.longitude = flt(longitude)
	doc.flags.ignore_permissions = True
	doc.insert()

	if content:
		file = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": f"bbhr-{doc.name}.{ext}",
				"content": content,
				"is_private": 1,
				"attached_to_doctype": "Employee Checkin",
				"attached_to_name": doc.name,
				"attached_to_field": "bbhr_photo",
			}
		)
		file.flags.ignore_permissions = True
		file.insert()
		doc.db_set("bbhr_photo", file.file_url, update_modified=False)

	attendance, warning = None, None
	if settings.create_attendance:
		attendance, warning = _sync_attendance(emp, date, [*logs, doc], doc.name)

	return _result(doc, attendance, warning)


def _result(doc, attendance, warning, replayed=False):
	t = get_datetime(doc.time)
	verb = _("Checked in") if doc.log_type == "IN" else _("Checked out")
	return {
		"ok": True,
		"replayed": replayed,
		"checkin": doc.name,
		"log_type": doc.log_type,
		"time": str(doc.time),
		"location": doc.get("bbhr_office_location"),
		"distance": doc.get("bbhr_distance"),
		"attendance": attendance,
		"warning": warning,
		"message": _("{0} at {1}").format(verb, t.strftime("%I:%M %p")),
	}


@frappe.whitelist(methods=["GET"])
def get_checkin_photo(checkin):
	"""Stream a punch selfie to someone allowed to see that employee."""
	row = frappe.db.get_value("Employee Checkin", checkin, ["employee", "bbhr_photo"], as_dict=True)
	if not row:
		frappe.throw(_("Check-in not found."), frappe.DoesNotExistError)
	perm.assert_can_view(row.employee)
	if not row.bbhr_photo:
		frappe.throw(_("No photo for this check-in."), frappe.DoesNotExistError)
	file = frappe.get_doc("File", {"file_url": row.bbhr_photo})
	frappe.local.response.filename = file.file_name
	frappe.local.response.filecontent = file.get_content()
	frappe.local.response.type = "download"
	frappe.local.response.display_content_as = "inline"
