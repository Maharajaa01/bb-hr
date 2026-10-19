frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["BB HR Department Today"] = {
	method: "bb_academy_hrms.bb_academy_hrms.dashboard_chart_source.bb_hr_department_today.bb_hr_department_today.get_data",
	filters: [],
};
