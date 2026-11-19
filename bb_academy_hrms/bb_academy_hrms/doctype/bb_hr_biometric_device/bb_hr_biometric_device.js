// Copyright (c) 2026, Maha Raja and contributors
// For license information, please see license.txt

frappe.ui.form.on("BB HR Biometric Device", {
	refresh(frm) {
		if (frm.is_new()) return;
		const group = __("Device Users");

		frm.add_custom_button(__("Fill Missing Device IDs"), () => {
			frappe.confirm(
				__("Give every active employee without an Attendance Device ID a number (taken from the employee ID where free)?"),
				() =>
					frm.call("fill_missing_device_ids").then((r) => show_assigned(r.message, __("Device IDs filled"))),
			);
		}, group);

		frm.add_custom_button(__("Send Employees to Device"), () => {
			if (!frm.doc.enabled) {
				frappe.msgprint(__("Enable this device first: a disabled device is not sent any commands."));
				return;
			}
			frappe.confirm(
				__("Create or update every active employee as a user on {0}? Missing Attendance Device IDs are filled first. Existing users keep their admin rights, password and card; only the name is updated.", [frm.doc.device_name || frm.doc.name]),
				() =>
					frm.call("send_employees_to_device").then((r) => {
						const m = r.message || {};
						let html = `<p>${__("{0} user(s) queued. The device collects them within about a minute while it is online.", [m.queued])}</p>`;
						if (m.assigned && m.assigned.length) html += assigned_table(m.assigned);
						if (m.skipped && m.skipped.length)
							html += `<p>${__("Skipped (fix the Attendance Device ID):")}</p><ul>${m.skipped.map((s) => `<li>${frappe.utils.escape_html(s)}</li>`).join("")}</ul>`;
						frappe.msgprint({ title: __("Employees sent"), message: html, indicator: "green" });
						frm.reload_doc();
					}),
			);
		}, group);

		frm.add_custom_button(__("View Commands"), () => {
			frappe.set_route("List", "BB HR Device Command", { device: frm.doc.name });
		}, group);

		show_command_status(frm);
	},
});

function show_command_status(frm) {
	frappe.call({
		method: "frappe.client.get_count",
		args: { doctype: "BB HR Device Command", filters: { device: frm.doc.name, status: ["in", ["Pending", "Sent"]] } },
		callback: (r) => {
			const waiting = r.message || 0;
			frappe.call({
				method: "frappe.client.get_count",
				args: { doctype: "BB HR Device Command", filters: { device: frm.doc.name, status: "Failed" } },
				callback: (f) => {
					const failed = f.message || 0;
					if (waiting) frm.dashboard.set_headline_alert(__("{0} command(s) waiting for the device.", [waiting]), "orange");
					else if (failed) frm.dashboard.set_headline_alert(__("{0} command(s) failed; see View Commands.", [failed]), "red");
				},
			});
		},
	});
}

function assigned_table(rows) {
	const body = rows
		.map((r) => `<tr><td>${frappe.utils.escape_html(r[0])}</td><td>${frappe.utils.escape_html(r[1] || "")}</td><td><b>${frappe.utils.escape_html(r[2])}</b></td></tr>`)
		.join("");
	return `<table class="table table-bordered table-sm"><thead><tr><th>${__("Employee")}</th><th>${__("Name")}</th><th>${__("Device ID")}</th></tr></thead><tbody>${body}</tbody></table>`;
}

function show_assigned(rows, title) {
	rows = rows || [];
	frappe.msgprint({
		title,
		message: rows.length ? assigned_table(rows) : __("Every active employee already has an Attendance Device ID."),
		indicator: "green",
	});
}
