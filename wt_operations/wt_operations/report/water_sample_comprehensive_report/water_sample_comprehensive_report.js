// Copyright (c) 2026, HM
// Water Sample Comprehensive Report

frappe.query_reports["Water Sample Comprehensive Report"] = {
	filters: [
		{
			fieldname: "site",
			label: __("Site / Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
		},
		{
			fieldname: "water_source",
			label: __("Water Source"),
			fieldtype: "Select",
			options: "\nInlet\nOutlet",
		},
		{
			fieldname: "sample_process_location",
			label: __("Sample Process Location"),
			fieldtype: "Data",
			// partial match (e.g. "Lifting" will match "Lifting tank")
		},
		{
			fieldname: "sample_type",
			label: __("Sample Type"),
			fieldtype: "Select",
			options: "\nIndustrial\nDomestic\nPotable",
			// adjust the option list above to match your actual Select options
		},
		{
			fieldname: "parameter",
			label: __("Parameter"),
			fieldtype: "Select",
			options: "\nCOD\npH\nTSS\nTurbidity.\nTDS.",
			// adjust to match all parameters used across your samples
		},
		{
			fieldname: "workflow_state",
			label: __("Workflow State"),
			fieldtype: "Select",
			options: "\nDraft\nCompleted",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nDraft\nSubmitted",
		},
		{
			fieldname: "compliance_status",
			label: __("Compliance"),
			fieldtype: "Select",
			options: "\nPass\nExceeds",
		},
		{
			fieldname: "responsible",
			label: __("Responsible"),
			fieldtype: "Link",
			options: "User",
		},
	],

	onload(report) {
		report.page.add_inner_button(__("Print"), () => download_pdf(report));
		report.page.add_inner_button(__("Export to Excel"), () => download_excel(report));
		report.page.add_inner_button(__("Monthly Print (Detailed)"), () => open_monthly_dialog());
	},
};

const REPORT_MODULE_PATH =
	"wt_operations.wt_operations.report.water_sample_comprehensive_report.water_sample_comprehensive_report";

function download_pdf(report) {
	// Calls the python function get_print_pdf_base64() via frappe.call (not a
	// raw download link). The PDF is built server-side, sent back as base64,
	// then opened in a new tab which auto-triggers the browser print dialog.
	const filters = report.get_values();

	frappe.call({
		method: REPORT_MODULE_PATH + ".get_print_pdf_base64",
		args: { filters: JSON.stringify(filters) },
		freeze: true,
		freeze_message: __("Generating PDF..."),
		callback: function (r) {
			if (!r.message) {
				frappe.msgprint(__("No data returned for the selected filters."));
				return;
			}

			const byteChars = atob(r.message);
			const byteNumbers = new Array(byteChars.length);
			for (let i = 0; i < byteChars.length; i++) {
				byteNumbers[i] = byteChars.charCodeAt(i);
			}
			const byteArray = new Uint8Array(byteNumbers);
			const blob = new Blob([byteArray], { type: "application/pdf" });
			const blobUrl = URL.createObjectURL(blob);

			const printWindow = window.open(blobUrl);
			if (printWindow) {
				printWindow.onload = function () {
					printWindow.print();
				};
			} else {
				frappe.msgprint(__("Please allow pop-ups to view/print the report."));
			}
		},
	});
}

function download_excel(report) {
	const filters = report.get_values();
	const url =
		"/api/method/" + REPORT_MODULE_PATH + ".download_excel" +
		"?filters=" + encodeURIComponent(JSON.stringify(filters));
	window.open(url);
}

function open_monthly_dialog() {
	const today = new Date();

	const d = new frappe.ui.Dialog({
		title: __("Monthly Detailed Print"),
		fields: [
			{
				fieldname: "month",
				label: __("Month (1-12)"),
				fieldtype: "Int",
				reqd: 1,
				default: today.getMonth() + 1,
			},
			{
				fieldname: "year",
				label: __("Year"),
				fieldtype: "Int",
				reqd: 1,
				default: today.getFullYear(),
			},
			{
				fieldname: "site",
				label: __("Site / Project (optional)"),
				fieldtype: "Link",
				options: "Project",
			},
		],
		primary_action_label: __("Generate PDF"),
		primary_action(values) {
			let url =
				"/api/method/" + REPORT_MODULE_PATH + ".download_monthly_pdf" +
				"?month=" + values.month + "&year=" + values.year;
			if (values.site) {
				url += "&site=" + encodeURIComponent(values.site);
			}
			window.open(url);
			d.hide();
		},
	});

	d.show();
}