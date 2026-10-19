"""Session bootstrap: who is signed in, which employee they are, and what they may open."""

import frappe
from frappe.utils import cint, today

from bb_academy_hrms.utils import permissions as perm


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_session():
	user = frappe.session.user
	if user == "Guest":
		return {"user": None}

	s = perm.scope(user)
	emp = s.employee
	full_name, user_image = frappe.db.get_value("User", user, ["full_name", "user_image"]) or (user, None)
	return {
		"user": {"name": user, "full_name": full_name or user, "image": user_image},
		"employee": {
			"name": emp.name,
			"employee_name": emp.employee_name,
			"first_name": emp.first_name,
			"designation": emp.designation,
			"department": emp.department,
			"company": emp.company,
			"image": emp.image,
			"status": emp.status,
			"date_of_joining": str(emp.date_of_joining) if emp.date_of_joining else None,
		}
		if emp
		else None,
		"roles": {
			"is_employee": bool(emp and emp.status == "Active"),
			"is_manager": bool(s.subordinates) or bool(s.is_manager),
			"is_hr": s.is_hr,
			"team_size": len(s.subordinates) if not s.is_hr else None,
		},
		"today": today(),
		"desk_access": frappe.db.get_value("User", user, "user_type") == "System User",
	}
