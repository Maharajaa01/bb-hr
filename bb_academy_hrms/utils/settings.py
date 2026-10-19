import frappe
from frappe.utils import cint


def get_settings():
	"""BB HR Settings with defaults filled in (works before anyone has saved the form)."""
	doc = frappe.get_cached_doc("BB HR Settings")
	return frappe._dict(
		enable_geofence=cint(doc.enable_geofence),
		default_radius=cint(doc.default_radius) or 150,
		accuracy_tolerance=cint(doc.accuracy_tolerance),
		max_accuracy=cint(doc.max_accuracy) or 200,
		require_photo=cint(doc.require_photo),
		min_gap_seconds=cint(doc.min_gap_seconds),
		create_attendance=cint(doc.create_attendance),
		office_locations=[
			frappe._dict(
				location_name=r.location_name,
				latitude=r.latitude,
				longitude=r.longitude,
				radius=cint(r.radius) or cint(doc.default_radius) or 150,
			)
			for r in doc.office_locations
			if r.enabled
		],
	)
