frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["BB HR My Attendance"] = {
	method: "bb_academy_hrms.bb_academy_hrms.dashboard_chart_source.bb_hr_my_attendance.bb_hr_my_attendance.get_data",
	filters: [],
};
