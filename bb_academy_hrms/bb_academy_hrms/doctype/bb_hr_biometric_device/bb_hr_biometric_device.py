# Copyright (c) 2026, Maha Raja and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class BBHRBiometricDevice(Document):
	"""A ZKTeco (ADMS push) attendance terminal allowed to post punches.

	Devices register themselves (disabled) the first time they contact the server;
	HR ticks Enabled to start accepting their punches. The status fields are written
	by bb_academy_hrms.integrations.zkteco_push.
	"""

	def before_insert(self):
		if not self.import_from:
			self.import_from = now_datetime()

	def validate(self):
		self.serial_number = (self.serial_number or "").strip()
		if not self.device_name:
			self.device_name = self.serial_number

	@frappe.whitelist()
	def fill_missing_device_ids(self):
		from bb_academy_hrms.integrations.zkteco_push import fill_missing_device_ids

		self._check_hr()
		return fill_missing_device_ids()

	@frappe.whitelist()
	def send_employees_to_device(self):
		from bb_academy_hrms.integrations.zkteco_push import fill_missing_device_ids, queue_employee_users

		self._check_hr()
		if not self.enabled:
			frappe.throw(frappe._("Enable this device first: a disabled device is not sent any commands."))
		assigned = fill_missing_device_ids()
		queued, skipped = queue_employee_users(self.name)
		return {"assigned": assigned, "queued": queued, "skipped": skipped}

	def _check_hr(self):
		self.check_permission("write")
		frappe.only_for(["HR Manager", "System Manager"])
		if not frappe.has_permission("Employee", "write"):
			frappe.throw(frappe._("You need write access to Employee to set Attendance Device IDs."), frappe.PermissionError)
