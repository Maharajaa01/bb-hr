# Copyright (c) 2026, Maha Raja and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class BBHRDeviceCommand(Document):
	"""A command queued for a ZKTeco device (ADMS). The device collects it on its next
	/iclock/getrequest poll and reports the result on /iclock/devicecmd; see
	bb_academy_hrms.integrations.zkteco_push."""
