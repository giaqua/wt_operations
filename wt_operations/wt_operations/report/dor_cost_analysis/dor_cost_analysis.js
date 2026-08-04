// ============================================================
// DOR Cost Analysis - Script Report client script
// Defines filters (date range, project, exclude-zero-volume,
// and the Cost / Cost per M3 / Both display toggle) and
// highlights the "/ M3" columns so they're easy to scan.
// ============================================================

frappe.query_reports["DOR Cost Analysis"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "exclude_zero_volume",
			label: __("Exclude Zero Treated Water"),
			fieldtype: "Check",
			default: 0,
		},
		{
			fieldname: "display",
			label: __("Show"),
			fieldtype: "Select",
			options: ["Both", "Cost Only", "Cost per M3 Only"],
			default: "Both",
			reqd: 1,
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (data && data.is_total_row) {
			value = `<b>${value}</b>`;
		}

		if (column.fieldname && column.fieldname.endsWith("_per_m3")) {
			value = `<span style="color:#1976a8; font-weight:600;">${value}</span>`;
		}

		return value;
	},
};