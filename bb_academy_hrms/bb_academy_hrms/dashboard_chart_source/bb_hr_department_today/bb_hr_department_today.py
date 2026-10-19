# Copyright (c) 2026, Maha Raja and contributors
# For license information, please see license.txt

import frappe

from bb_academy_hrms.api import desk


@frappe.whitelist()
def get_data(
	chart_name=None,
	chart=None,
	no_cache=None,
	filters=None,
	from_date=None,
	to_date=None,
	timespan=None,
	time_interval=None,
	heatmap_year=None,
):
	# no @cache_source on purpose: see bb_academy_hrms/api/desk.py
	return desk.hr_department_today()
