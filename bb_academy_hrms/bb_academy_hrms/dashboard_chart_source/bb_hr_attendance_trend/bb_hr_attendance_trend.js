frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["BB HR Attendance Trend"] = {
	method: "bb_academy_hrms.bb_academy_hrms.dashboard_chart_source.bb_hr_attendance_trend.bb_hr_attendance_trend.get_data",
	filters: [],
};
