# Copyright (c) 2026, Maha Raja and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from bb_academy_hrms.utils.geo import is_valid_coordinate


class BBHRSettings(Document):
	def validate(self):
		seen = set()
		for row in self.office_locations:
			if not is_valid_coordinate(row.latitude, row.longitude):
				frappe.throw(_("Row {0}: enter a valid latitude and longitude.").format(row.idx))
			key = row.location_name.strip().lower()
			if key in seen:
				frappe.throw(_("Row {0}: location {1} is listed twice.").format(row.idx, row.location_name))
			seen.add(key)

		if self.enable_geofence and not any(r.enabled for r in self.office_locations):
			frappe.msgprint(
				_("Geofence is on but no office location is enabled, so every check-in will be refused."),
				indicator="orange",
				alert=True,
			)
