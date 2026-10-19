"""Salary slips. Confidential: only the employee themself and HR - never reporting managers."""

import frappe
from frappe import _
from frappe.utils import cint, flt

from bb_academy_hrms.utils import permissions as perm

LIST_FIELDS = [
	"name",
	"employee",
	"employee_name",
	"start_date",
	"end_date",
	"posting_date",
	"currency",
	"gross_pay",
	"total_deduction",
	"net_pay",
	"rounded_total",
	"payment_days",
	"total_working_days",
	"salary_structure",
]
PRINT_FORMAT = "Salary Slip Standard"


def recent_slips(employee, limit=3):
	return frappe.get_all(
		"Salary Slip",
		filters={"employee": employee, "docstatus": 1},
		fields=LIST_FIELDS,
		order_by="start_date desc",
		limit=limit,
		ignore_permissions=True,
	)


def _resolve(employee):
	if employee:
		perm.assert_can_view(employee, salary=True)
		return employee
	return perm.require_employee().name


def _load_slip(name):
	"""Fetch a submitted slip after checking the caller may see whose it is."""
	employee = frappe.db.get_value("Salary Slip", {"name": name, "docstatus": 1}, "employee")
	if not employee:
		frappe.throw(_("Salary slip not found."), frappe.DoesNotExistError)
	perm.assert_can_view(employee, salary=True)
	return frappe.get_doc("Salary Slip", name)


@frappe.whitelist(methods=["GET"])
def get_salary_slips(employee=None, year=None, page=1, page_length=12):
	employee = _resolve(employee)
	filters = {"employee": employee, "docstatus": 1}
	if cint(year):
		filters["start_date"] = ["between", [f"{cint(year)}-01-01", f"{cint(year)}-12-31"]]
	page, page_length = max(cint(page), 1), min(max(cint(page_length), 1), 50)
	rows = frappe.get_all(
		"Salary Slip",
		filters=filters,
		fields=LIST_FIELDS,
		order_by="start_date desc",
		start=(page - 1) * page_length,
		page_length=page_length,
		ignore_permissions=True,
	)
	total = frappe.db.count("Salary Slip", filters)
	years = frappe.db.sql(
		"select distinct year(start_date) from `tabSalary Slip` where employee=%s and docstatus=1 order by 1 desc",
		employee,
		pluck=True,
	)
	return {
		"employee": employee,
		"employee_name": frappe.db.get_value("Employee", employee, "employee_name"),
		"rows": rows,
		"total": total,
		"page": page,
		"page_length": page_length,
		"years": years,
	}


@frappe.whitelist(methods=["GET"])
def get_salary_slip(name):
	doc = _load_slip(name)

	def lines(table):
		return [
			{"component": r.salary_component, "abbr": r.abbr, "amount": flt(r.amount)}
			for r in table
			if flt(r.amount) or not r.get("do_not_include_in_total")
		]

	return {
		"name": doc.name,
		"employee": doc.employee,
		"employee_name": doc.employee_name,
		"designation": doc.designation,
		"department": doc.department,
		"company": doc.company,
		"start_date": str(doc.start_date),
		"end_date": str(doc.end_date),
		"posting_date": str(doc.posting_date),
		"currency": doc.currency,
		"salary_structure": doc.salary_structure,
		"payroll_frequency": doc.payroll_frequency,
		"total_working_days": flt(doc.total_working_days),
		"payment_days": flt(doc.payment_days),
		"absent_days": flt(doc.absent_days),
		"leave_without_pay": flt(doc.leave_without_pay),
		"earnings": lines(doc.earnings),
		"deductions": lines(doc.deductions),
		"gross_pay": flt(doc.gross_pay),
		"total_deduction": flt(doc.total_deduction),
		"net_pay": flt(doc.net_pay),
		"rounded_total": flt(doc.rounded_total),
		"total_in_words": doc.total_in_words,
		"bank_name": doc.bank_name,
		"bank_account_no": ("•••• " + str(doc.bank_account_no)[-4:]) if doc.bank_account_no else None,
	}


@frappe.whitelist(methods=["GET"])
def download_salary_slip(name):
	"""PDF of a submitted slip. Scope is checked in _load_slip, so the print-permission check is skipped."""
	doc = _load_slip(name)
	print_format = (
		PRINT_FORMAT if frappe.db.exists("Print Format", {"name": PRINT_FORMAT, "disabled": 0}) else None
	)
	previous = frappe.flags.ignore_print_permissions
	frappe.flags.ignore_print_permissions = True
	try:
		pdf = frappe.get_print("Salary Slip", doc.name, print_format=print_format, doc=doc, as_pdf=True)
	finally:
		frappe.flags.ignore_print_permissions = previous

	frappe.local.response.filename = f"{doc.name.replace('/', '-')}.pdf"
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "pdf"
