"""Face-verified check-in.

The first punch with face verification on enrols the employee's face; every later punch
must match it. All matching runs here; the client only captures frames.

A scan is a few frames looking straight at the camera ("front") and, when the liveness
check is on, a few frames taken while the employee turns their head in a direction the
server picked at random ("turn"). The turn must actually show the head rotating that way
and still be the same face, which a printed photo or a still on another screen cannot do.

Guards, in order:
  1. too many failed scans lock face check-in for this employee for 15 minutes,
  2. the liveness challenge is single-use, short-lived and bound to the employee,
  3. every front frame shows exactly one sharp, well-lit, frontal face, all the same person,
  4. the turn frames show that same face rotated the requested way,
  5. the front frames match the enrolled template (cosine >= threshold).
"""

import json
import secrets

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from bb_academy_hrms.utils import face as engine
from bb_academy_hrms.utils import permissions as perm
from bb_academy_hrms.utils.settings import get_settings

PROFILE = "BB HR Face Profile"
CHALLENGE_TTL = 180
LOCKOUT_SECONDS = 15 * 60
MAX_FRONT, MAX_TURN = 3, 4
SAME_SCAN_MIN = 0.5  # front frames of one scan must agree at least this much
TURN_SAME_FACE_MIN = 0.3  # pose change lowers similarity, so the turn frame gets a looser bar
MIN_TURN = 0.15  # yaw change (eye-widths) that counts as a deliberate head turn
ADAPT_MARGIN = 0.12  # a match this far above threshold is added to the template
MAX_ADAPTIVE = 5


def _challenge_key(token):
	return f"bbhr:face_challenge:{token}"


def _failure_key(employee):
	return f"bbhr:face_failures:{employee}"


def _profile(employee):
	name = frappe.db.exists(PROFILE, {"employee": employee})
	return frappe.get_doc(PROFILE, name) if name else None


def _samples(profile):
	"""(enrolled, adaptive) embedding lists, or None when the profile needs re-enrolling."""
	if not profile or profile.model_version != engine.MODEL_VERSION:
		return None
	try:
		data = json.loads(profile.embeddings or "{}")
	except ValueError:
		return None
	enrolled = data.get("enrolled") or []
	return (enrolled, data.get("adaptive") or []) if enrolled else None


def is_enrolled(employee):
	return _samples(_profile(employee)) is not None


def status_for(employee, settings=None):
	settings = settings or get_settings()
	return {
		"enabled": bool(settings.face_verification),
		"liveness": bool(settings.face_liveness),
		"enrolled": bool(settings.face_verification) and is_enrolled(employee),
	}


def _check_lockout(employee, settings):
	if cint(frappe.cache.get_value(_failure_key(employee), expires=True)) >= settings.face_max_failures:
		frappe.throw(
			_(
				"Too many face scans did not match. Face check-in is paused for 15 minutes; ask HR if you need help."
			),
			title=_("Face Check Locked"),
			exc=frappe.PermissionError,
		)


def _record_failure(employee):
	key = _failure_key(employee)
	frappe.cache.set_value(
		key, cint(frappe.cache.get_value(key, expires=True)) + 1, expires_in_sec=LOCKOUT_SECONDS
	)


def _fail(message, employee=None):
	"""Refuse the scan. Passing `employee` counts it towards the lockout (identity/liveness failures only)."""
	if employee:
		_record_failure(employee)
	frappe.throw(message, title=_("Face Not Verified"))


# ------------------------------------------------------------------- endpoints
@frappe.whitelist(methods=["POST"])
def challenge():
	"""Start a scan: which way to turn, and a one-time token to send back with the punch."""
	emp = perm.require_employee()
	settings = get_settings()
	if not settings.face_verification:
		return {"enabled": False}
	_check_lockout(emp.name, settings)
	token = secrets.token_urlsafe(24)
	direction = secrets.choice(("left", "right"))
	frappe.cache.set_value(
		_challenge_key(token), {"employee": emp.name, "direction": direction}, expires_in_sec=CHALLENGE_TTL
	)
	return {
		"enabled": True,
		"token": token,
		"direction": direction,
		"liveness": bool(settings.face_liveness),
		"enrolled": is_enrolled(emp.name),
		"expires_in": CHALLENGE_TTL,
	}


# ------------------------------------------------------------ used by punch()
def _parse(payload):
	if isinstance(payload, str):
		try:
			payload = json.loads(payload)
		except ValueError:
			payload = None
	if not isinstance(payload, dict):
		frappe.throw(
			_("A face scan is required to check in. Allow camera access and scan your face."),
			title=_("Face Scan Required"),
		)
	front, turn = payload.get("front"), payload.get("turn") or []
	if not isinstance(front, list) or not front or not isinstance(turn, list):
		frappe.throw(_("The face scan was incomplete. Please scan again."), title=_("Face Scan Required"))
	return str(payload.get("token") or ""), front[:MAX_FRONT], turn[:MAX_TURN]


def _consume_challenge(token, employee):
	key = _challenge_key(token)
	data = frappe.cache.get_value(key, expires=True) if token else None
	frappe.cache.delete_value(key)
	if not data or data.get("employee") != employee:
		frappe.throw(_("The face scan expired. Please scan again."), title=_("Scan Expired"))
	return data["direction"]


def _analyse(content, require_frontal):
	try:
		return engine.analyse(content, require_frontal=require_frontal)
	except engine.FaceError as e:
		frappe.throw(str(e), title=_("Face Not Verified"))
	except Exception:
		frappe.log_error(title="BB HR: face engine failed")
		frappe.throw(
			_("Face verification is not available on the server right now. Please tell HR."),
			title=_("Face Check Unavailable"),
		)


def verify_scan(emp, payload, settings=None):
	"""Check a punch's face scan against the employee's enrolment, enrolling on first use.

	Returns dict(status="Enrolled"|"Verified", score, photo=(bytes, ext)). Throws when refused.
	"""
	from bb_academy_hrms.api.attendance import _decode_photo

	settings = settings or get_settings()
	_check_lockout(emp.name, settings)
	token, front_raw, turn_raw = _parse(payload)
	direction = _consume_challenge(token, emp.name) if settings.face_liveness else None
	if direction and not turn_raw:
		frappe.throw(_("The face scan was incomplete. Please scan again."), title=_("Face Scan Required"))

	front_files = [_decode_photo(f) for f in front_raw]
	fronts = [_analyse(content, require_frontal=True) for content, _ext in front_files]
	embeddings = [f["embedding"] for f in fronts]
	for i in range(len(embeddings)):
		for j in range(i + 1, len(embeddings)):
			if engine.cosine(embeddings[i], embeddings[j]) < SAME_SCAN_MIN:
				_fail(
					_(
						"Your face changed during the scan. Hold the phone steady and keep only yourself in view."
					),
					emp.name,
				)
	probe = engine.centroid(embeddings)

	if direction:
		base_yaw = sum(f["yaw"] for f in fronts) / len(fronts)
		sign = -1 if direction == "left" else 1  # frames are mirrored: your left is image left
		turned = []
		for raw in turn_raw:
			try:
				turned.append(engine.analyse(_decode_photo(raw)[0], require_frontal=False))
			except engine.FaceError:
				continue  # a frame mid-turn may be blurry or partly out of view; others may be fine
			except Exception:
				frappe.log_error(title="BB HR: face engine failed")
		best = max(turned, key=lambda f: sign * (f["yaw"] - base_yaw), default=None)
		if not best or sign * (best["yaw"] - base_yaw) < MIN_TURN:
			_fail(
				_(
					"We didn't see you turn your head to the {0}. Scan again and turn slowly when asked."
				).format(_("left") if direction == "left" else _("right")),
				emp.name,
			)
		if engine.cosine(best["embedding"], probe) < TURN_SAME_FACE_MIN:
			_fail(_("A different face appeared while you turned. Please scan again."), emp.name)

	profile = _profile(emp.name)
	samples = _samples(profile)
	if samples is None:
		_enroll(emp, profile, embeddings, front_files[0])
		return {"status": "Enrolled", "score": None, "photo": front_files[0]}

	enrolled, adaptive = samples
	score = engine.cosine(probe, engine.centroid(enrolled + adaptive))
	if score < settings.face_threshold:
		_fail(
			_(
				"Your face does not match the face enrolled for {0}. Try again in good light, or ask HR to reset your face enrolment."
			).format(emp.employee_name),
			emp.name,
		)

	if score >= settings.face_threshold + ADAPT_MARGIN:
		# follow slow changes (beard, glasses, ageing) only from confident matches
		adaptive = [*adaptive, [round(v, 6) for v in probe]][-MAX_ADAPTIVE:]
	profile.db_set(
		{
			"embeddings": json.dumps({"enrolled": enrolled, "adaptive": adaptive}),
			"samples": len(enrolled) + len(adaptive),
			"last_verified_on": now_datetime(),
			"last_score": round(score, 3),
			"verified_count": cint(profile.verified_count) + 1,
		},
		update_modified=False,
	)
	frappe.cache.delete_value(_failure_key(emp.name))
	return {"status": "Verified", "score": round(score, 3), "photo": front_files[0]}


def _enroll(emp, profile, embeddings, photo):
	enrolled = [[round(v, 6) for v in e] for e in embeddings]
	if profile:  # stale model version or unreadable data: start over on the same record
		profile.delete(ignore_permissions=True)
	profile = frappe.new_doc(PROFILE)
	profile.employee = emp.name
	profile.employee_name = emp.employee_name
	profile.enrolled_on = now_datetime()
	profile.model_version = engine.MODEL_VERSION
	profile.samples = len(enrolled)
	profile.embeddings = json.dumps({"enrolled": enrolled, "adaptive": []})
	profile.flags.ignore_permissions = True
	profile.insert()

	content, ext = photo
	file = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"bbhr-face-{emp.name}.{ext}",
			"content": content,
			"is_private": 1,
			"attached_to_doctype": PROFILE,
			"attached_to_name": profile.name,
			"attached_to_field": "enrollment_photo",
		}
	)
	file.flags.ignore_permissions = True
	file.insert()
	profile.db_set("enrollment_photo", file.file_url, update_modified=False)
	frappe.cache.delete_value(_failure_key(emp.name))
