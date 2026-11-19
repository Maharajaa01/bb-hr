import frappe


def execute():
	"""New Settings fields have no stored value on an existing Single, so their defaults never apply."""
	defaults = {
		"enable_face_verification": 1,
		"face_liveness": 1,
		"face_match_threshold": 0.42,
		"face_max_failures": 5,
	}
	for field, value in defaults.items():
		stored = frappe.db.sql(
			"select value from `tabSingles` where doctype='BB HR Settings' and field=%s", field
		)
		if not stored or stored[0][0] in (None, ""):
			frappe.db.set_single_value("BB HR Settings", field, value)
	frappe.clear_document_cache("BB HR Settings", "BB HR Settings")
