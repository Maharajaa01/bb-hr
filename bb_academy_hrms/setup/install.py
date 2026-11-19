"""Install / migrate hooks: custom fields on Employee Checkin and default settings."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CHECKIN_FIELDS = {
	"Employee Checkin": [
		{
			"fieldname": "bbhr_section",
			"fieldtype": "Section Break",
			"label": "BB HR",
			"insert_after": "shift_actual_end",
			"collapsible": 1,
		},
		{
			"fieldname": "bbhr_office_location",
			"fieldtype": "Data",
			"label": "Office Location",
			"insert_after": "bbhr_section",
			"read_only": 1,
		},
		{
			"fieldname": "bbhr_distance",
			"fieldtype": "Float",
			"label": "Distance From Office (m)",
			"insert_after": "bbhr_office_location",
			"read_only": 1,
			"precision": "1",
		},
		{
			"fieldname": "bbhr_accuracy",
			"fieldtype": "Float",
			"label": "GPS Accuracy (m)",
			"insert_after": "bbhr_distance",
			"read_only": 1,
			"precision": "1",
		},
		{
			"fieldname": "bbhr_column_break",
			"fieldtype": "Column Break",
			"insert_after": "bbhr_accuracy",
		},
		{
			"fieldname": "bbhr_photo",
			"fieldtype": "Attach Image",
			"label": "Check-in Photo",
			"insert_after": "bbhr_column_break",
			"read_only": 1,
		},
		{
			"fieldname": "bbhr_request_id",
			"fieldtype": "Data",
			"label": "Request ID",
			"insert_after": "bbhr_photo",
			"read_only": 1,
			"unique": 1,
			"no_copy": 1,
			"hidden": 1,
		},
		{
			"fieldname": "bbhr_face_status",
			"fieldtype": "Select",
			"label": "Face Check",
			"options": "\nVerified\nEnrolled",
			"insert_after": "bbhr_request_id",
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "bbhr_face_score",
			"fieldtype": "Float",
			"label": "Face Match Score",
			"insert_after": "bbhr_face_status",
			"read_only": 1,
			"precision": "3",
			"no_copy": 1,
		},
	]
}


def after_install():
	after_migrate()


def after_migrate():
	create_custom_fields(CHECKIN_FIELDS, update=True)
	fetch_face_models()


def fetch_face_models():
	"""Best effort: a failed download must not break migrate; the first face scan retries it."""
	from bb_academy_hrms.utils import face

	try:
		face.download_models()
	except Exception as e:
		print(f"BB HR: could not download face models now ({e}); they will be fetched on first use.")


def sync():
	"""Install only this app's schema on a live site without a full `bench migrate`:

	bench --site <site> execute bb_academy_hrms.setup.install.sync
	"""
	for name in ("bb_hr_office_location", "bb_hr_settings", "bb_hr_face_profile"):
		frappe.reload_doc("bb_academy_hrms", "doctype", name, force=True)
	after_migrate()
	frappe.db.commit()
	print("BB HR schema synced.")
